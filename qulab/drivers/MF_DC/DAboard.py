
import socket
import time
import sys

from types import coroutine
from . import DAboard_defines
import struct
import math
from itertools import repeat
from collections import Counter
import asyncio

class DABoard(object):
    """
        DA 板对象

        实现与DA硬件的连接，

        """

    def __init__(self):
        self.board_def  = DAboard_defines.DABoard_Defines()
        self.port       = 80
        self.zeros      = list(repeat(0,1024))
        self.channel_amount = 4
        # Initialize core parameters
        # Create a TCP/IP socket
        self.sockfd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sockfd.settimeout(5.0)
        self.soft_version = None

    def connect(self, addr):
        """Connect to Server"""
        #host = '149.199.131.176'
        host = addr
        print ('Host name is: {}'.format(host))
        try:
            self.sockfd.connect((host, self.port))
            print ('connected')
            # rcv_data = self.Read_RAM(0x80000000, 1024)
            # self.soft_version = [int(rcv_data[718]),int(rcv_data[717]),int(rcv_data[716])]
            return 1
        except socket.error as msg:
            self.sockfd.close()
            self.sockfd = None
        if self.sockfd is None:
            print ('ERROR:Could not open socket')
            return -1


    def disconnect(self):
        """Close the connection to the server."""
        if self.sockfd is not None:
            print ('Closing socket')
            self.sockfd.close()

    def Write_Reg(self, bank, addr, data):
        """Write to register command."""
        cmd = self.board_def.CMD_WRITE_REG
        #I need to pack bank into 4 bytes and then only use the 3
        packedBank = struct.pack("l", bank)
        unpackedBank = struct.unpack('4b', packedBank)

        packet = struct.pack("4bLL", cmd, unpackedBank[0], unpackedBank[1], unpackedBank[2], addr, data)
    #     print ('this is my packet: {}'.format(repr(packet)))
        #Next I need to send the command
        try:
            self.send_data(packet)
        except socket.timeout:
            print ("Timeout raised and caught")
        #next read from the socket
        try:
            stat, data = self.receive_data()
        except socket.timeout:
            print ("Timeout raised and caught")
        if stat != 0x0:
            print ('Issue with Write Command stat: {}'.format(stat))
            return self.board_def.STAT_ERROR

        return self.board_def.STAT_SUCCESS

    def Read_Reg(self, bank, addr, data=0):
        """Read from register command."""
        # data is used for spi write
        cmd = self.board_def.CMD_READ_REG
        # data = 0xFAFAFAFA

        #I need to pack bank into 4 bytes and then only use the 3
        packedBank = struct.pack("l", bank)
        unpackedBank = struct.unpack('4b', packedBank)

        packet = struct.pack("4bLi", cmd, unpackedBank[0], unpackedBank[1], unpackedBank[2], addr, data)
        #Next I need to send the command
        try:
            self.send_data(packet)
        except socket.timeout:
            print ("Timeout raised and caught")
        #next read from the socket
        try:
            self.recv_stat, self.recv_data = self.receive_data()
        except socket.timeout:
            print ("Timeout raised and caught")

        if self.recv_stat != 0x0:
            print ('Issue with Reading Register stat={}!!!'.format(self.recv_stat) )
            return self.board_def.STAT_ERROR
        return self.recv_data

    def Read_RAM(self, addr, length):
        """Read from RAM command."""
        cmd = self.board_def.CMD_READ_MEM
        pad = 0xFAFAFA

        #I need to pack bank into 4 bytes and then only use the 3
        packedPad = struct.pack("l", pad)
        unpackedPad = struct.unpack('4b', packedPad)

        packet = struct.pack("4bLL", cmd, unpackedPad[0], unpackedPad[1], unpackedPad[2], addr, length)
        #Next I need to send the command
        self.send_data(packet)
        #next read from the socket
        recv_stat, recv_data = self.receive_data()
        if recv_stat != 0x0:
            print ('Issue with Reading RAM stat: {}'.format(recv_stat))
            return self.board_def.STAT_ERROR
        ram_data = self.receive_RAM(int(length))
        return ram_data

    def Write_RAM(self, start_addr, wave, ram_sel = 0):
        """Write to RAM command."""
        cmd = self.board_def.CMD_WRITE_MEM
        pad = ram_sel
        #I need to pack bank into 4 bytes and then only use the 3
        packedPad = struct.pack("L", pad)
        unpackedPad = struct.unpack('4b', packedPad)
        length = len(wave) << 1 #short 2 byte
        packet = struct.pack("4bLL", cmd, unpackedPad[0], unpackedPad[1], unpackedPad[2], start_addr, length)
        #Next I need to send the command
        self.send_data(packet)
        #next read from the socket
        recv_stat, recv_data = self.receive_data()
        if recv_stat != 0x0:
            print ('Ram Write cmd Error stat={}!!!'.format(recv_stat))
            return self.board_def.STAT_ERROR
        #method 1
        # format = str(len(wave))+'H'
        # format = "{0}d".format(len(wave))
        format = "{0:d}H".format(len(wave))
        packet = struct.pack(format, *wave)
        # print(packet[0:64])
        # format = '{:02x}{:02x}-'*32
        # print(format.format(*(packet[0:64])))
        #method 2
        # packet = struct.pack('H'*len(wave), *wave)
        #method 3
        # packet = b''.join(struct.pack('H', elem) for elem in wave)

        self.send_data(packet)
        #Use a while loop to send all the data in the data array
        # while sent_data < (length/4):
        # #    print ('this is my RAM data: {}'.format(hex(data[sent_data])))
        #     ram_packet = struct.pack("L", data[sent_data])
        #     self.send_data(ram_packet)
        #     sent_data = sent_data + 1

        #next read from the socket to ensure no errors occur
        self.sockfd.settimeout(20)
        stat, data = self.receive_data()
        self.sockfd.settimeout(5)
        # print(packet)
        if stat != 0x0:
            print ('Ram Write Error stat={}!!!'.format(stat))
            return self.board_def.STAT_ERROR

    def Run_Command(self, ctrl, data0, data1):
        """Run command."""

        cmd = self.board_def.CMD_CTRL_CMD
        packedCtrl = struct.pack("l", ctrl)
        unpackedCtrl = struct.unpack('4b', packedCtrl)
        packet = struct.pack("4bLL", cmd, unpackedCtrl[0], unpackedCtrl[1], unpackedCtrl[2], data0, data1)
    #    print ('this is my cmd packet: {}'.format(repr(packet)))
    #     print(ctrl, data0, data1)
        self.send_data(packet)
        stat, data = self.receive_data()
        if stat != 0x0:
            print ('Dump RAM Error stat={}!'.format(stat))
        return data

    def send_data(self, msg):
        """Send data over the socket."""
        totalsent = 0
        # tt= struct.unpack('c'*len(msg), msg)
        # print(tt)
        while totalsent < len(msg):
            sent = self.sockfd.send(msg)
            if sent == 0:
                raise RuntimeError("Socket connection broken")
            totalsent = totalsent + sent

    def receive_data(self):
        """Read received data from the socket."""
        chunks = []
        bytes_recd = 0
        while bytes_recd < 8:
            #I'm reading my data in byte chunks
            chunk = self.sockfd.recv(min(8 - bytes_recd, 4))
            if chunk == '':
               raise RuntimeError("Socket connection broken")
            chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
        stat_tuple = struct.unpack('L', chunks[0])
        data_tuple = struct.unpack('L', chunks[1])
        stat = stat_tuple[0]
        data = data_tuple[0]
        return stat, chunks[1]

    def receive_RAM(self, length):
        """Read received data from the socket after a read RAM command."""
        chunks = []
        ram_data = b''
        bytes_recd = 0
        self.sockfd.settimeout(5)
        # self.sockfd.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
        while bytes_recd < length:
            #I'm reading my data in byte chunks
            chunk = self.sockfd.recv(min(length - bytes_recd, length))
            #Unpack the received data
            # data = struct.unpack("L", chunk)
            # print(len(chunk))
            ram_data += chunk
            if chunk == '':
               raise RuntimeError("Socket connection broken")
            # chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
        # print(bytes_recd)
        #  print ('Print something I can understand: {}'.format(repr(chunks)))
        #  print ram_data
        return ram_data

    def SpiReadWrite(self, R_W=1, spi_dev=2, spi_sel=3, reg_addr=0, reg_data=0):
        # R_W 1 read 0 write
        # spi_dev = 2 读LTC2000A的SPI， 1 读9516,9136的SPI，0读配置FLASH的SPI（一般禁止）
        # spi_sel 在spi_dev = 1时  0表示9516， 1表示9136-1 2表示9136-2
        # reg_data 写入的数据，仅低8位有效
        addr = (spi_dev << 24) | (spi_sel << 16) | reg_addr | (R_W << 7)
        tmp = self.Read_Reg(self.board_def.BANK_SPI, addr, reg_data)
        return struct.unpack('i', tmp)[0]
        # return tmp

    def SetRamRead(self,flag):
        # 1 read lower data
        self.Run_Command(self.board_def.CTRL_READ_FLAG,flag,0)
