#   FileName:硬件board.py
#   Author:
#   E-mail:
#   All right reserved.
#   Modified: 2019.2.18
#   Description:The class of 硬件
import os
import socket
import time
import numpy as np

from . import BoardDefines
import struct

class RAWBoard(object):
    """
        硬件设备 板对象

        实现与硬件的连接，提供基础访问接口

        4个基础函数::
        
        - ``init`` 完成硬件对象的初始化
        - ``connect`` 完成硬件对象的连接，在连接成功后会给出硬件对象的版本标识
        - ``disconnect`` 断开与硬件的连接
        - ``receive_data`` 完成硬件发送的网络数据的接收
        - ``send_data`` 完成向硬件发送网络数据

        4个基础命令::

        - ``Write_Reg`` 写寄存器，完成硬件对象各模块的参数配置写入
        - ``Read_Reg`` 读寄存器，完成硬件对象各模块的参数配置读出
        - ``Read_RAM`` 读存储区，完成硬件各通道数据存储区的读出
        - ``Write_RAM`` 写存储区，完成硬件各通道数据存储区的写入

        1个基础状态读取::

        - ``Read_Status_Block`` 读取硬件状态包命令
        """

    def __init__(self):

        self.board_def = BoardDefines.BoardDefines()
        self.port = 80
        self.dev_id = 'device 01'
        self.dev_ip = '0.0.0.0'
        # Create a TCP/IP socket
        self.sockfd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sockfd.settimeout(5.0)
        self.soft_version = 1.1

    def connect(self, host, dev_id=None):
        """
        :param dev_id: 可选的设备标识，如果没有给，会以IP的后两个数做设备标识
        :param host: 硬件 板的IP地址
        :return:
        :notes::

            连接硬件，连接成功，读取板上的版本标识
            连接失败，返回错误，并打印错误消息，关闭socket
        """
        self.dev_ip = host
        
        try:
            self.sockfd.connect((host, self.port))
            print('连接成功')
            # 读取硬件ID
            self.dev_id = self.Read_Reg(8, 0, 0)
            print(f'device IP: {self.dev_ip}, ID: {self.dev_id}')
            return 1
        except socket.error as msg:
            self.sockfd.close()
            self.sockfd = None
            print(f'ERROR:{msg}')
        if self.sockfd is None:
            print(f'ERROR:{host}:Socket打开失败')
            return -1
        

    def disconnect(self):
        """
        :return: None
        :notes::

            断开当前硬件对象的连接
        """
        if self.sockfd is not None:
            print('Closing socket')
            self.sockfd.close()

    def Write_Reg(self, bank, addr, data):
        """
        :param bank: 寄存器对象所属的BANK（设备或模块），4字节
        :param addr: 偏移地址，4字节
        :param data: 待写入数据，4字节
        :return: 4字节，写入是否成功，此处的成功是指TCP/IP协议的成功，也可以等效为数据写入成功

        :notes::

            这条命令下，硬件对象返回8字节数据，4字节表示状态，4字节表示数据

        """
        cmd = self.board_def.CMD_WRITE_REG
        packet = struct.pack(">LLLL", cmd, bank, addr, data)
        try:
            self.send_data(packet)
        except socket.timeout:
            print("Timeout raised and caught")
        stat = 0
        try:
            stat, data, data2 = self.receive_data()
        except socket.timeout:
            print("Timeout raised and caught")
        if stat != 0x0:
            print('Issue with Write Command stat: {}'.format(stat))
            return self.board_def.STAT_ERROR
        return self.board_def.STAT_SUCCESS

    def Read_Reg(self, bank, addr, data=0):
        """
        :param bank: 寄存器对象所属的BANK（设备或模块），4字节
        :param addr: 偏移地址，4字节
        :param data: 待写入数据，4字节
        :return: 4字节，读取是否成功，如果成功，返回读取的数据，否则，返回错误状态

        """
        cmd = self.board_def.CMD_READ_REG
        packet = struct.pack(">LLLL", cmd, bank, addr, data)
        try:
            self.send_data(packet)
        except socket.timeout:
            print("Timeout raised and caught")
        recv_stat = 0
        recv_data = 0
        try:
            recv_stat, recv_data, recv_data2 = self.receive_data()

        except socket.timeout:
            print("Timeout raised and caught")

        if recv_stat != 0x0:
            print('Issue with Reading Register stat={}!!!'.format(recv_stat))
            return self.board_def.STAT_ERROR
        if bank == 8:
            return '{:X}'.format((recv_data2<<16)+(recv_data>>16))
        return recv_data

    def Read_RAM(self, bank, addr, length):
        """
        :param bank: 数据对象所属的BANK（设备或模块），4字节
        :param addr: 读取存储区的起始地址
        :param length: 读取存储区的数据长度
        :return: 读取成功的数据或读取失败的错误状态

        :notes::

        """
        cmd = self.board_def.CMD_READ_MEM
        packet = struct.pack(">LLLL", cmd, bank, addr, length)
        self.send_data(packet)
        # next read from the socket, read length has 20 byte head
        recv_stat, ram_data = self.receive_RAM(int(length + 20))
        if recv_stat != 0x0:
            print('Issue with Reading RAM stat: {}'.format(recv_stat))
            return self.board_def.STAT_ERROR

        return ram_data, recv_stat

    def Write_RAM(self, bank, start_addr, data, length):
        """
        :param bank: 数据对象所属的BANK（设备或模块），4字节
        :param start_addr: 写入存储区的起始地址
        :param data: 写入存储区的数据,数据是byts类型的list
        :param length: 写入存储区的数据长度
        :return: 写入成功或失败的错误状态
        """
        cmd = self.board_def.CMD_WRITE_MEM
        packet = struct.pack(">LLLL", cmd, bank, start_addr, length)
        packet = packet + data
        self.send_data(packet)
        recv_stat, recv_data, recv_data2 = self.receive_data()
        if recv_stat != 0x0:
            print('Ram Write cmd Error stat={}!!!'.format(recv_stat))
            return self.board_def.STAT_ERROR

    def send_data(self, data):
        """
        :param data:  待发送数据的字节流
        :return: 命令发送状态（已发送字节数）
        """
        totalsent = 0
        while totalsent < len(data):
            sent = self.sockfd.send(data)
            if sent == 0:
                raise RuntimeError("Socket connection broken")
            totalsent = totalsent + sent
        return totalsent

    def receive_data(self):
        """
        :return: 20字节数据，网络接口接收到的数据，仅限4条基础指令的响应数据，5个4字节，20字节长
        :notes::
            从网络接口接收数据，接收到的是发送方发送的数据加上读请求返回的寄存器数据

            +-------------+----------------------+----------------+------------+----------+
            | 写寄存器标识| 模块标识             | 寄存器偏移地址 | 写寄存器值 | 返回值   |
            +-------------+----------------------+----------------+------------+----------+
            | 0xAAAAAAAA  | 32位(见模块标识定义) | 32位           | 32位       | 0表示正常|
            +-------------+----------------------+----------------+------------+----------+
            | 读寄存器标识| 模块标识             | 寄存器偏移地址 | 写寄存器值 | 返回值   |
            +-------------+----------------------+----------------+------------+----------+
            | 0x55555555  | 32位(见模块标识定义) | 32位           | 32位       | 0表示正常|
            +-------------+----------------------+----------------+------------+----------+
            | 写RAM标识   | 模块标识             | 寄存器偏移地址 | 写寄存器值 | 返回值   |
            +-------------+----------------------+----------------+------------+----------+
            | 0x55AAAA55  | 32位(见模块标识定义) | 32位           | 32位       | 0表示正常|
            +-------------+----------------------+----------------+------------+----------+
        """
        chunks = b''
        bytes_recd = 0
        while bytes_recd < 20:
            tmp = self.sockfd.recv(min(20 - bytes_recd, 20))
            if tmp == '':
                raise RuntimeError("Socket connection broken")
            chunks += tmp
            bytes_recd = bytes_recd + len(tmp)
        stat_tuple = struct.unpack('>LLLLL', chunks)
        stat = stat_tuple[-1]
        data = stat_tuple[-2]
        data2 = stat_tuple[-3]
        return stat, data, data2

    def receive_RAM(self, length):
        """
        :param length: 待读取的字节数
        :return: length字节数据，网络接口接收到的数据，仅限读取RAM和status包使用
        :notes::
            从网络接口接收数据，长度以字节为单位
            该命令配合``Read_RAM``或``Read_Status_RAM``指令实现大批量数据的读取

            +-------------+----------------------+----------------+------------+----------+
            | 读RAM标识   | 模块标识             | 寄存器偏移地址 | 读回数据   | 返回值   |
            +-------------+----------------------+----------------+------------+----------+
            | 0xAA5555AA  | 32位(见模块标识定义) | 32位           | 最大1MB    | 0表示正常|
            +-------------+----------------------+----------------+------------+----------+

        """
        ram_data = b''
        bytes_recd = 0
        self.sockfd.settimeout(5)
        while bytes_recd < length:
            chunk = self.sockfd.recv(min(length - bytes_recd, length))
            ram_data += chunk
            if chunk == '':
                raise RuntimeError("Socket connection broken")
            bytes_recd = bytes_recd + len(chunk)

        return ram_data[:-4], ram_data[-4:-1]
    