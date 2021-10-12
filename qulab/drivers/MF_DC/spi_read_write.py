import math
import struct
import time
from functools import reduce
from . import DAboard
import matplotlib.pyplot as plt
import numpy as np

class SpiControl(DAboard.DABoard):
    def __init__(self):
        super().__init__()

    def spi_set_config(self):
        data = 0x200012;
        for i in range(0,12):
        
            data0 = 0x20 | ((i*2+1) << 24);
            #print(i)
            self.Run_Command(self.board_def.CTRL_DATA_SPI, data0, data);
            
            data0 = 0x22 | ((i*2+1) << 24)
            self.Run_Command(self.board_def.CTRL_DATA_SPI, data0, 0)
            
    def spi_set_voltage(self, bank, data):
        '''
        :param self:
        :param bank: spi模块编号, 0 spi0, 1 spi1
        :param addr: spi模块寄存器空间偏移地址
        :param data: spi模块寄存器写入数据
        :return: None
        notes::

            数据获取模块寄存器写入
            地址范围0-15，每个地址4字节数据
        '''
        #if(data > 0):
            #data1 = 0x180000 + data/10*524288;
            #print(data1)
        #elif(data==0):
            #data1 = 0x180000;
        #elif(data < 0):
        data1 = 0x180000 + data/10*524288;
        data1 = int(data1)
        data0 = 0x20 | (((bank-1)*2+1) << 24)
        #print(self.board_def.CTRL_DATA_SPI, hex(data0), hex(data1))
        self.Run_Command(self.board_def.CTRL_DATA_SPI, int(data0), int(data1))
        data0 = 0x22 | ((bank*2+1) << 24)
        self.Run_Command(self.board_def.CTRL_DATA_SPI, int(data0), 0)

    def spi_read_voltage(self, bank):
        '''
        :param self:
        :param bank: spi模块编号, 0 spi0, 1 spi1
        :param addr: 寄存器偏移地址，范围（0-15）
        :return: 对应地址的寄存器数据
        notes::

            数据获取模块寄存器读取
            地址范围0-15，每个地址4字节数据
        '''

        data0 = 0x20 | (((bank-1)*2+2) << 24)
        reg_data = self.Run_Command(self.board_def.CTRL_DATA_SPI, data0, 0)
        cnt = struct.unpack('I', reg_data)
        #print(hex(cnt[0]))
        cnt = float(cnt[0]);
        
        if(cnt<0x180000):
            vol = -0.000000019*(0x180000 - cnt);
        else:
            vol = 0.000000019*(cnt - 0x180000);

        data0 = 0x22 | ((bank*2+2) << 24)
        reg_data = self.Run_Command(self.board_def.CTRL_DATA_SPI, data0, 0)
        cnt = struct.unpack('I', reg_data)
        print(vol,'V')

if __name__ == '__main__':
    

    spi = SpiControl()
    new_ip = '192.168.1.170'

    board_status = spi.connect(new_ip)
    print(spi.spi_write_reg(1, 3, 1234567))
    print(spi.spi_read_reg(1, 3))
