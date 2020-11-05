#   FileName:TrigGboard.py
#   Author:
#   E-mail:
#   All right reserved.
#   Modified: 2019.10.16
#   Description:The class of trigger board
import os
import socket
import time
import numpy as np

from . import RawBoard
import struct


class TrigBoard(RawBoard.RAWBoard):
    def __init__(self, ch_num=16):
        super().__init__()
        self.CH_NUM      = ch_num
        self.trig_freq   = [0]*self.CH_NUM
        self.trig_count  = [0]*self.CH_NUM
        self.trig_offset = [0]*self.CH_NUM
        self.trig_width  = [0]*self.CH_NUM

    def set_bit(self, reg, bit_pos):
        mask = 1 << bit_pos
        # print(hex(reg | mask))
        return reg | mask
    
    def unset_bit(self, reg, bit_pos):
        mask = 1 << bit_pos
        mask = 0xFFFFFFFF ^ mask
        # print(hex(reg & mask))
        return reg & mask

    def clock_switch_ext(self):
        '''switch to externel clock source'''
        _reg = self.Read_Reg(4, 0x04C)
        _reg = self.set_bit(_reg, 0)
        self.Write_Reg(4, 0x04C, _reg)

    def clock_switch_int(self):
        '''switch to internel clock source'''
        _reg = self.Read_Reg(4, 0x04C)
        _reg = self.unset_bit(_reg, 0)
        self.Write_Reg(4, 0x04C, _reg)

    def set_sel_clock(self):
        '''set sel clock signal'''
        _reg = self.Read_Reg(4, 0x04C)
        _reg = self.set_bit(_reg, 2)
        self.Write_Reg(4, 0x04C, _reg) 

    def unset_sel_clock(self):
        '''set sel clock signal'''
        _reg = self.Read_Reg(4, 0x04C)
        _reg = self.unset_bit(_reg, 2)
        self.Write_Reg(4, 0x04C, _reg) 
        
    def set_SSW_CTRL_A(self):
        '''set sel clock signal'''
        _reg = self.Read_Reg(4, 0x04C)
        _reg = self.set_bit(_reg, 3)
        self.Write_Reg(4, 0x04C, _reg) 

    def unset_SSW_CTRL_A(self):
        '''set sel clock signal'''
        _reg = self.Read_Reg(4, 0x04C)
        _reg = self.unset_bit(_reg, 3)
        self.Write_Reg(4, 0x04C, _reg) 

    def set_SSW_CTRL_B(self):
        '''set sel clock signal'''
        _reg = self.Read_Reg(4, 0x04C)
        _reg = self.set_bit(_reg, 4)
        self.Write_Reg(4, 0x04C, _reg) 

    def unset_SSW_CTRL_B(self):
        '''set sel clock signal'''
        _reg = self.Read_Reg(4, 0x04C)
        _reg = self.unset_bit(_reg, 4)
        self.Write_Reg(4, 0x04C, _reg) 
        
    def trig_switch_ext(self):
        '''switch to externel trigger source'''
        self.Write_Reg(4, 0x044, 0)

    def trig_switch_int(self):
        '''switch to internel trigger source'''
        self.Write_Reg(4, 0x044, 1)

    def start_internal_trig(self, channel=0):
        '''start internel trigger source, channel==0 start all channel'''
        assert channel in range(0, self.CH_NUM+1)
        reg_val = 0xFFFF
        if channel > 0: 
            reg_val = 1 << (channel - 1)
        self.Write_Reg(4, 0x048, reg_val)
    
    def disable_trig_output(self, channel=0):
        '''disable trigger output, channel==0 disable all channel'''
        assert channel in range(0, self.CH_NUM+1)
        reg_val = 0x00000000
        if channel > 0: 
            reg_val = 0xFFFFFFFF ^ (1 << (channel - 1))
        _val = self.Read_Reg(4, 0x040)
        reg_val = reg_val & _val
        self.Write_Reg(4, 0x040, reg_val)
    
    def enable_trig_output(self, channel=0):
        '''enable trigger output, channel==0 enable all channel'''
        assert channel in range(0, self.CH_NUM+1)
        reg_val = 0x0000
        if channel > 0: 
            reg_val = 1 << (channel - 1)
        _val = self.Read_Reg(4, 0x040)
        reg_val = reg_val | _val 
        self.Write_Reg(4, 0x040, reg_val)
    
    def set_trig_count(self, channel, count):
        '''set the trig count of channel, channel==0 set all channel
           count == 0 , output infinit trig pluees
        '''
        assert channel in range(0, self.CH_NUM+1)
        if count == 0:
            print('output infinit trig pluses')
        else:
            print('output {0:g} trig pluses'.format(count))

        if channel == 0:
            print('set trig count for all channel')
            for i in range( self.CH_NUM):
                self.Write_Reg(4, 0x80+(i) * 4, count)
        else:
            self.Write_Reg(4, 0x80+(channel-1) * 4, count)

    def set_trig_freq(self, channel, freq, width=0):
        '''set the trig freq of channel, channel==0 set all channel
           freq unit is Hz
           width unit is s, width == 0, output 50% duty pulse
        '''
        assert channel in range(0, self.CH_NUM+1)
        cnt = int(250000000/ freq)
        act_freq = int(250000000/cnt)
        print('set trig frequency to:{:g}Hz'.format(act_freq))
        _width = int(width / 4e-9)
        act_width = _width*4e-9
        assert _width < cnt - 4, 'width is to high'
        if _width < 5: 
            print(r'set trig width to 50% duty cycle')
        else:
            print('set trig width to:{0:g} second'.format(act_width))

        if channel == 0:
            print('set trig frequency for all channel')
            for i in range( self.CH_NUM):
                self.Write_Reg(4, 0x180+(i) * 4, cnt-1)
                self.Write_Reg(4, 0x200+(i) * 4, _width)
        else:
            self.Write_Reg(4, 0x180+(channel-1) * 4, cnt)
            self.Write_Reg(4, 0x200+(channel-1) * 4, _width)

    def set_trig_offset(self, channel, offet_time):
        ''' set the trig offset of channel, time resolution is 10 ps, time unit is ps
            channel==0 set all channel
        '''
        assert channel in range(0, self.CH_NUM+1)
        print('trig offset set to {:g} ps'.format(offet_time))
        coarse_cnt = int(offet_time/4000)
        fine_cnt = int((offet_time - coarse_cnt*4000)/5)
        tap1 = fine_cnt
        tap2 = 0
        if fine_cnt > 400:
            tap1 = 400
            tap2 = fine_cnt - 400

        self.Write_Reg(5, 0x4, tap1)
        self.Write_Reg(5, 0x8, tap2)
        self.Write_Reg(5, 0xC, 0)
        self.Write_Reg(5, 0x10, 0)
        if channel == 0:
            print('set trig offset for all channel')
            for i in range( self.CH_NUM):
                self.Write_Reg(4, 0x100+(i) * 4, coarse_cnt)
                self.Write_Reg(5, 0x0, 0 << (i))
                self.Write_Reg(5, 0x0, 1 << (i))
        else:
            self.Write_Reg(4, 0x100+(channel-1) * 4, coarse_cnt)
            self.Write_Reg(5, 0x0, 0 << (channel-1))
            self.Write_Reg(5, 0x0, 1 << (channel-1))
    
    def set_internal_trig(self, channel=0, freq=10000, offet_time =0, count=0, width=0):
        '''default set all channel to 10kHz, 50% duty, infinit trig pulses, offset is 0'''
        self.set_trig_count(channel, count)
        self.set_trig_freq(channel, freq, width)
        self.set_trig_offset(channel, offet_time)
    
    def clkclock_spi_write(self, reg_addr, reg_data):
        # print(f'config clock:addr{hex(reg_addr)}, data:{hex(reg_data)}')
        self.Write_Reg(4, 0x14<<2, (3 << 16) | reg_addr)
        self.Write_Reg(4, 0x14<<2, (4 << 16) | reg_data)
        time.sleep(0.01)

    def clkclock_spi_read(self, reg_addr):
        self.Write_Reg(4, 0x14<<2, (3 << 16) | reg_addr | 0x8000)
        self.Write_Reg(4, 0x14<<2, (4 << 16))
        self.Write_Reg(4, 0x14<<2, (5 << 16))
        ret = self.Read_Reg(4, 0x14<<2)
        return ret & 0xFFFF
    
    def config_clock(self, ref_clock='10MHz'):
        cfg = []
        if ref_clock == '10MHz':
            clock_config = self.board_def.REF_10MHz_CONFIG
        else:
            clock_config = self.board_def.REF_250MHz_CONFIG
        for l in clock_config:
            pos = l.find('spi1_wr')
            if pos > 0:
                cfg.append(l[pos+7:].strip())
        paras = []
        for l in cfg:
            para = [int(i,16) for i in l.split(' ')]
            paras.append([para[0], para[1]])
        for p in paras:
            self.clkclock_spi_write(p[0], p[1])

    def _channel_info(self, channel):
        if self.Read_Reg(4, 0x44) == 0:
            info = 'chanel:{0} is use external trigger'.format(channel)
            return info
        trig_freq   = 1/(self.Read_Reg(4, 0x180+(channel-1) * 4)*4e-9)
        trig_width  = self.Read_Reg(4, 0x200+(channel-1) * 4) 
        if trig_width == 0:
            trig_width = 1/trig_freq
        else:
            trig_width = trig_width * 4e-9

        trig_count  = self.Read_Reg(4, 0x80+(channel-1) * 4) 
        if trig_count == 0:
            trig_count = 'infinit'
        
         
        corse_cnt = self.Read_Reg(4, 0x100+(channel-1) * 4)
        fine_tap1 = self.Read_Reg(5, 0x100+(channel-1) * 4)
        fine_tap2 = self.Read_Reg(5, 0x100+(channel-1) * 4)
        fine_tap3 = self.Read_Reg(5, 0x100+(channel-1) * 4)
        fine_tap4 = self.Read_Reg(5, 0x100+(channel-1) * 4)
        trig_offset = corse_cnt * 4000 + (fine_tap1+fine_tap2+fine_tap3+fine_tap4)*5
        info_fmt = 'chanel:{:g}, frequency:{:g} Hz, pulse width:{:g} second, trig count:{:g}, offset:{:g}ps'
        info = info_fmt.format(trig_freq, trig_width, trig_count, trig_offset)
        return info

    def display_info(self):
        for ch in range(1,self.CH_NUM+1):
            print(self._channel_info(ch))