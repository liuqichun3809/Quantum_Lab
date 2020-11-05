# coding=utf-8
import socket
import struct
import time
import os
from os import path
# from queue import Queue
import numpy as np
import itertools 
import logging

class board(object):
    """
    [base hardware define, surport basic read reg, write reg, read memory, write memory]
    """    
    def __init__(self, dev_type = 'Board'):
        self.client = None
        self.ip_port = None
        self.port = 80
        self.dev_type = dev_type
        self.dev_id = None
        self.dev_ip = '0.0.0.0'
        self.soft_version = 1.2
        self.network_frame_size = 1032
        self.fill_data = struct.pack('LL', 0xFFFFFFFF, 0xFFFFFFFF)
        self.clear_view = memoryview(bytearray(4096))
        self.BUFSIZE = 1024 * 1024 * 10
        self.timeout = 0.01
        self.view_start = 0
        self.data_size = 19
        self.bytes_data = None#bytearray(512 * 1024 * 1032)

    def gen_log(self, name):
        self.log = logging.getLogger(name)
        self.log.propagate = 0
        if not self.log.handlers:
            streamhandler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
            streamhandler.setFormatter(formatter)
            self.log.addHandler(streamhandler)
        # print(self.log)
        # log = self.log
    def connect(self, ip, client=None):  
        """[connect hardware]
        
        Arguments:
            ip {[str]} -- [the hardware ip address]
        
        Keyword Arguments:
            dev_id {[num]} -- [the mac address of the hardware] (default: {None})
        """
        
        if not client:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.client.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.BUFSIZE*2)
            self.client.settimeout(self.timeout)
        else:
            self.client = client
        self.dev_ip = ip
        self.gen_log(ip)
        # self.set_debug_level(logging.WARNING)
        self.ip_port = (ip, 0x1234)
        self._reset_ddr()
        self.set_speed()
        self.get_network_info()
        self.set_count_ip()
        
    def disconnect(self):
        """"
        断开设备连接
        """
        self.client.close()

    def set_debug_level(self, level):
        self.log.setLevel(level)

    def reg_ops(self, reg_list, need_return = True):
        """[read/write upto 127 32 bit data from regs, packet format:
        8 byte head, 全0即可
        后面每8字节对应一个寄存器操作：1字节读写，1字节BANK ID，2字节offset，4字节数据
        ]
        
        Arguments:
            reg_list {[2D list]} -- [reg [R/W, bank, addr, data] paired list to be read/write]
        
        Keyword Arguments:
            need_return {bool} -- [description] (default: {True})
        """
        assert len(reg_list) < 128
        cmd = struct.pack('II', 0,0)
        #     reg_para = [i>>1 for i in range(80)]
        reg_para = list(itertools.chain(*reg_list))
        fmt = 'BBHI'*len(reg_list)
        para = struct.pack(fmt, *reg_para)
        msg = cmd + para + self.fill_data * (128 - len(reg_list))
        try_cnt = 5
        
        for i in range(try_cnt):
            try:
                self.client.sendto(msg, self.ip_port)
                if not need_return:
                    # time.sleep(0.01)
                    return 0
                self.client.settimeout(0.1)
                ret = self.client.recvfrom(4096)
                self.client.settimeout(self.timeout)
                break
            except:
                if i == 4:
                    self.log.critical(f'{self.dev_id} reg ops faild')
                    return [0]*4*len(reg_list)
                else:
                    self.log.debug(f'{self.dev_id} reg ops try {i}')
                self.clear_udp_buf()
        # return struct.unpack(fmt, ret[0][8:len(reg_list)*8+8])
        return struct.unpack(fmt, ret[0][self.network_frame_size-1024:len(reg_list)*8+self.network_frame_size-1024])

    def read_regs(self, reg_list):
        """[read upto 127 32 bit data from regs]
        
        Arguments:
            reg_list {[2D list]} -- [reg [bank, addr, data] paired list to be read] 
        
        Keyword Arguments:
            need_return {bool} -- [description] (default: {True})
        """
        for idx in range(len(reg_list)):
            reg_list[idx] = [0]+reg_list[idx]
        st = self.reg_ops(reg_list)
        # print(st)
        return st
        # return self.reg_ops(reg_list)

    def write_regs(self, reg_list, need_return=True):
        """[write upto 127 32 bit data to regs]
        
        Arguments:
            bank {[u8]} -- [reg module to be selected]
            reg_list {[2D list]} -- [reg [bank, addr, data] paired list to be write]
        
        Keyword Arguments:
            need_return {bool} -- [description] (default: {True})
        """
        for idx in range(len(reg_list)):
            reg_list[idx] = [1]+reg_list[idx]
        return self.reg_ops(reg_list, need_return=need_return)

    def read_ram(self, module_id, ram_sel, start_addr):
        """[read upto 1024 byte from ram[module_id][ram_sel][start_addr]]
        
        Arguments:
            module_id {[u8]} -- [module number to be selected, bram range is 16-31]
            ram_sel {[u8]} -- [ram number to be selected, only low 7 bit is active]
            start_addr {[u24]} -- [write start byte address,  should be 8 byte aligned]
        """
        assert module_id in range(16,32), ram_sel < 128
        cmd = struct.pack('IHBB', module_id, start_addr & 0xFFFF, start_addr >> 16, 0x80 & ram_sel)
        msg = cmd + self.fill_data * 128
        self.client.sendto(msg, self.ip_port)
        ret = self.client.recvfrom(4096)
        return ret
    
    def set_count_ip(self):
        # print(self.client.getsockname())
        self.write_regs([[0x50, 0x5C, 0],[0x50, 0x5C, 1]])

    def get_frame_cnt(self):
        return(self.read_regs([[0x50,0x58, 0]])[-1])

    def write_ram(self, module_id, ram_sel, start_addr, ram_data):
        """[write upto 1024 byte to ram[module_id][ram_sel][start_addr]]
        
        Arguments:
            module_id {[u8]} -- [module number to be selected, bram range is 16-31]
            ram_sel {[u8]} -- [ram number to be selected, only low 7 bit is active]
            start_addr {[u24]} -- [write start byte address,  should be 8 byte aligned]
            ram_data {[bytes array]} -- [write data,  should be multiple of 8 bytes]
        """
        # assert module_id in range(16,32), ram_sel < 128
        assert type(ram_data) is type(b'0')
        assert len(ram_data) & 0x7 == 0
        repeats = (len(ram_data) + 1023) >> 10
        for i in range(5):
            try:
                _start_addr = start_addr
                _s_cnt = self.get_frame_cnt()+1
                for i in range(repeats):
                    msg = struct.pack('HBBI', _start_addr & 0xFFFF, _start_addr >> 16, 0x00 | ram_sel, module_id<<24)
                    msg += ram_data[(i<<10):(i+1)<<10]
                    # print('msg length', len(msg))
                    self.client.sendto(msg, self.ip_port)
                    _start_addr += 1024
                _e_cnt = self.get_frame_cnt()
                if _e_cnt - _s_cnt == repeats:
                    return True
                self.log.debug('ram write cnt:{0}, expected:{1}'.format(_e_cnt-_s_cnt, repeats))
            except:
                self.log.debug('{0} write ram time out'.format(self.dev_id))
                self.clear_udp_buf()
        return False

    def write_uart(self, module_id=32, ram_sel=0, start_addr=0, ram_data=None):
        """[write upto 1024 byte to ram[module_id][ram_sel][start_addr]]
        
        Arguments:
            module_id {[u8]} -- [module number to be selected, bram range is 32]
            ram_sel {[u8]} -- [ram number to be selected, 0]
            start_addr {[u24]} -- [write start byte address,  0]
            ram_data {[bytes array]} -- [write data,  should be multiple of 8 bytes]
        """
        # assert module_id in range(16,32), ram_sel < 128
        assert type(ram_data) is type(b'0')
        assert len(ram_data) & 0x7 == 0
        repeats = (len(ram_data) + 1023) >> 10
        for i in range(5):
            try:
                _start_addr = start_addr
                for i in range(repeats):
                    msg = struct.pack('HBBI', _start_addr & 0xFFFF, _start_addr >> 16, 0x00 | ram_sel, module_id<<24)
                    msg += ram_data[(i<<10):(i+1)<<10]
                    # print('msg length', len(msg))
                    self.client.sendto(msg, self.ip_port)
                    _start_addr += 1024
                return True
            except:
                self.log.debug('{0} write uart ram time out'.format(self.dev_id))
        return False

    def get_network_info(self):
        # self.dev_ip   = hex(self.read_regs([[0x50, 0x20, 0]])[-1])
        self.dev_mask = hex(self.read_regs([[0x50, 0x24, 0]])[-1])
        self.dev_gw   = hex(self.read_regs([[0x50, 0x28, 0]])[-1])
        dev_macl = self.read_regs([[0x50, 0x2c, 0]])[-1]
        dev_mach = self.read_regs([[0x50, 0x30, 0]])[-1]
        self.dev_id= '{:04X}'.format(dev_mach) + '{:08X}'.format(dev_macl)

    def clear_udp_buf(self):
        # self._stop_read_ddr()
        # print('clear udp buf')
        try:
            while True:
                self.client.recv_into(self.clear_view, self.network_frame_size)
        except:
            pass

    def set_speed(self):
        self.generate_zero_copy(2048*1032)
        data_size = [20-i for i in range(10)]
        for size in data_size:
            for j in range(10):
                self.data_size = size
                self._stop_read_ddr()
                self.clear_udp_buf()
                # time.sleep(0.01)
                self.client.settimeout(self.timeout*(j+1))
                status, _ = self._read_ddr_block(1, 0, 0, 1 << self.data_size, test_speed=True)
                if not status:
                    break
            if status:
                # print(f'Device connect successful, readout data size unit is: {1 << (self.data_size - 10)}kB, frame gap time is: {self.frame_gap * (100 / 15.625)}ns')
                self.log.info('Device connect successful, readout data size unit is: %skB'%(1 << (self.data_size - 10)))
                self.bytes_data = None
                return True
        self.log.error('!!! Device connect failed, please check network connection')
        self.bytes_data = None
        self.clear_udp_buf()
        return False

    def reduce_read_size(self):
        '''reduce the readout block size'''
        # self.client.close()
        # self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # self.client.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.BUFSIZE*2)
        # self.client.settimeout(self.timeout)
        time.sleep(1)
        self.data_size =  self.data_size - 1 if self.data_size > 12 else self.data_size
        err_msg = 'warnning: current network or cpu load is high, the data transmit unit will set to %skB!!!'%(1 << (self.data_size - 10))
        self.clear_udp_buf()
        self.log.warning(err_msg)
        assert self.data_size > 12, 'error: network data read failed'

    def _reset_ddr(self, module_id=1):     
        self.write_regs([[module_id, 0x10, 1], [module_id, 0x10, 0]])

    def _stop_read_ddr(self, module_id=1):
        """[summary]
        
        Keyword Arguments:
            module_id {int} -- [ddr module id in cpu] (default: {1})
        """
        self.write_regs([[module_id, 0x40, 1]], need_return=False)
        self.write_regs([[module_id, 0x40, 0]], need_return=True)

    def start_ddr_read(self, module_id=1, start_addr=0, read_len=4096):
        """[check if the selected ddr module is ready to read
        0x20	DST_IP      |   0x40	     DDR_RD_STOP 
        0x24	PKT_MODE    |   0x44	     DDR_RD_START    
        0x28	PKT_LEN     |   0x48	     DDR_RD_ADDR  
        0x2C	TDEST       |   0x4C	     DDR_RD_LEN 
        ]
        
        Arguments:
            module_id {[unsigned]} -- [ddr module number]
        
        Returns:
            [bool] -- [cmd set is success or not]
        """        
        logging.debug('ddr read: addr:{0}, len:{1}'.format(start_addr, read_len))
        # wait ddr read idle
        for i in range(1000):
            ddr_busy = self.read_regs([[module_id, 0x64, 0]])[-1] & 0x01
            if ddr_busy == 0:
                break
        if ddr_busy:
            self.log.warning('memory is busy')
            self._reset_ddr()
        cmd = []
        cmd.append([module_id, 0x20, 0])
        cmd.append([module_id, 0x24, 0])
        cmd.append([module_id, 0x28, 0])
        cmd.append([module_id, 0x2c, 0])
        cmd.append([module_id, 0x48, start_addr])
        cmd.append([module_id, 0x4c, read_len])
        cmd.append([module_id, 0x44, 0])
        cmd.append([module_id, 0x44, 1])
        cmd.append([module_id, 0x44, 0])
        self.write_regs(cmd, need_return=False)
        # time.sleep(0.05)

    def read_ddr(self, module_id=1, start_addr=0, read_len=4096, test_speed=False):
        """[read data from ddr, read_len should be 4kB aligned
            将读取数据分成多次 1<<self.data_size大小的读取
        ]
        
        Arguments:
            module_id {[unsigned]} -- [which ddr to be read]
            start_addr {[unsigned]} -- [start read byte address, should be 4kB aligned]
            read_len {[unsigned]} -- [bytes to be readout, read_len should be 4kB aligned]
        """    
        assert module_id in range(1,16)
        assert read_len & 0xFFF == 0, hex(read_len)
        _cur_addr = start_addr
        _cur_view = self.view_start
        _left_size = read_len
        while _left_size > 0:
            _cur_rd_len = 1 << self.data_size if _left_size > (1 << self.data_size) else _left_size 
            # print('read ddr', _cur_addr, _cur_rd_len, _cur_addr + _cur_rd_len)
            sta, read_bytes = self._read_ddr_block(module_id, _cur_view, _cur_addr, _cur_rd_len)
            _left_size -= read_bytes
            _cur_addr += read_bytes
            _cur_view += read_bytes
            if not sta:
                return False
        self.view_start += read_len
        return True

    def _read_ddr_block(self, module_id=1, view_start=0, start_addr=0, read_len=4096, test_speed=False):
        """[read data from ddr, read_len should be 4kB aligned 
        and less than 1 << self.data_size
        步骤：
        1. 发送寄存器控制命令，设置读起始地址，长度，启动
        2. 等待接收数据，如果不成功，再次尝试，最多尝试10次, 
           在做速度测试的时候只尝试一次
        ]
        
        Arguments:
            module_id {[unsigned]} -- [which ddr to be read]
            start_addr {[unsigned]} -- [start read byte address, should be 4kB aligned]
            read_len {[unsigned]} -- [bytes to be readout, read_len should be 4kB aligned]
        
        Returns:
            [type] -- [description]
        """        
        # assert module_id in range(1,16)
        # assert read_len & 0xFFF == 0
        frame_cnt = read_len >> 10
        try_cnt = 1 if test_speed else 5 
        for retry_cnt in range(try_cnt):
            view = memoryview(self.bytes_data)
            view = view[(view_start>>10)*self.network_frame_size:]
            self.start_ddr_read(module_id, start_addr, read_len)
            try:
                for i in range(frame_cnt):
                    self.client.recv_into(view, self.network_frame_size)
                    view = view[self.network_frame_size:]
                return True, read_len
            except:
                if self.bytes_data is None:
                    self.log.critical('no zero copy memory is set')
                    return False, 0
                self.log.debug('retry:{0}, frame:{1}, start:0x{2:X}, len:0x{3:X}'.format(retry_cnt,i,start_addr, read_len))
                self._stop_read_ddr()
                self.clear_udp_buf()

        if not test_speed:
            self.reduce_read_size()
        return False, 0

    def write_ddr(self, module_id=1, start_addr=0, data=None):
        """[write data to ddr, length of data should be 4kB aligned
        步骤：
        1. 清零DDR写入帧计数
        2. 将数据拆成1kB单元，每一包加上头部，发送到DDR
        3. 回读DDR写入帧计数，如果与写入不符，重新写入
        ]
        
        Arguments:
            module_id {[unsigned]} -- [which ddr to be write]
            start_addr {[unsigned]} -- [start write byte address, should be 4kB aligned]
            data {[bytes]} -- [bytes data to be write, length of data should be 4kB aligned]
        
        Returns:
            [bool] -- [description]
        """        
        length = len(data)
        assert module_id in range(1,16)
        assert type(data) is type(b'0')
        assert length & 0x3FF == 0, 'data size {0} shuled be multiple of 1024 byte'.format(length)
        frame_cnt = length >> 10
        for try_cnt in range(5):
            try:
                _s_cnt = self.get_frame_cnt()+1
                for i in range(frame_cnt):
                    head = struct.pack('II', start_addr+(i<<10), module_id<<24)
                    msg = head + data[i<<10:(i+1)<<10]
                    self.client.sendto(msg, self.ip_port)
                _e_cnt = self.get_frame_cnt()
                if _e_cnt - _s_cnt == frame_cnt:
                    return True
                self.log.debug('ddr write cnt:{0}, expected:{1}'.format(_e_cnt-_s_cnt, frame_cnt))
            except:
                self.log.debug('retry count:{0}'.format(try_cnt))
                time.sleep(try_cnt*0.1)
                self.clear_udp_buf()
        self.log.critical('write ddr faild')
        return False
    
    def check_data(self, size):
        network_frame_cnt = size >> 10
        end_pos = network_frame_cnt*1032
        raw_data = np.frombuffer(self.bytes_data[0:end_pos], dtype='u2')
        all_data1 = np.reshape(raw_data, (network_frame_cnt, 516))[:, 4:]
        cnt_arr = np.reshape(all_data1, (1, network_frame_cnt*512))[0]
        # if sample false data, the recieved data is unsigned 16bit counter
        self.log.info('start check data, data size is %skB'%(size >> 10))
        with open('ddr_data.dat', 'wb') as f:
            f.write(self.bytes_data[:end_pos])
        expect_arr = np.linspace(0, (size>>1)-1, (size>>1), dtype=cnt_arr.dtype)
        ext_cnt = 0 
        try:
            assert (cnt_arr == expect_arr).all(), 'memory data read test failed!'
            self.log.info('memory data read test is passed!')
        except:
            expect_count = 0
            for idx, i in enumerate(cnt_arr):
                if i != expect_arr[idx]:
                    self.log.critical('idx:%s, i:%s not equal expect_count:%s'%(idx, i,expect_arr[idx] ))
                    ext_cnt = 1
                    break
                expect_count += 1
                expect_count %= 65536
        self.bytes_data = None
        try:
            assert ext_cnt == 0
        except:
            print('ddr data error')
            self._reset_ddr()
    def generate_zero_copy(self, size):
        self.bytes_data = bytearray(size)
        self.view_start = 0

    def ddr_self_test(self, start_addr = 0, size = 100, data = None):
        self.clear_udp_buf()
        _s = time.time()
        self.view_start = 0
        self.log.info('read write ddr self test size: {0} MB'.format(size))
        data = [i for i in range(65536)]*8 if data is None else [data]*(1<<19) #512*1024个数据
        b_data = np.asarray(data, dtype='u2').tobytes() #1MB数据
        self.generate_zero_copy((size << 10) * 1032)
        repeat = size
        for i in range(repeat):
            self.write_ddr(1,start_addr+(i<<20),b_data)
        _t1 = time.time()
        for i in range(repeat):
            self.read_ddr(1, start_addr+(i<<20), 1024*1024)
        _t2 = time.time()
        _t_total = round(_t2-_s, 3)
        _t_write = round(_t1-_s, 3)
        _t_read = round(_t2-_t1, 3)
        self.log.info('time elapsed total:{0}s, write:{1}s, read:{2}'.format(_t_total, _t_write, _t_read))
        self.check_data(repeat<<20)
        return _t_total, _t_write, _t_read

    def ram_self_test(self, module_id=None):
        data = [i for i in range(65536)]  #64k个数据
        size = len(data)>>9
        b_data = np.asarray(data, dtype='u2').tobytes() #128kB数据
        # repeat = size
        id = 0x10 if module_id is None else module_id
        self.write_ram(id, 0, 0, b_data)
        self.log.info('writeram self test size: {0} kB passed'.format(size))

    def _write_eeprom(self, addr, data):
        module_id = 0x20
        dev_addr = 0x52
        self.write_regs([[module_id, 0x040, 0x0A]])
        self.write_regs([[module_id, 0x020, 0xD0]])
        self.write_regs([[module_id, 0x108, 0x100 | (dev_addr<<1)]])
        self.write_regs([[module_id, 0x108, addr]])
        self.write_regs([[module_id, 0x108, 0x200 | data]])
        self.write_regs([[module_id, 0x100, 0x0D]])
        time.sleep(0.01)
        d = self.read_eeprom(addr)
        if d != data:
            self.log.error(f'write eeprom error, write: {data}, read: {d}')
            return 1
        return 0
    def write_eeprom(self, addr, data):
        assert addr >= 0x80
        self._write_eeprom(addr, data)

    def set_eeprom_para(self, para_idx, para):
        assert para_idx < 32
        self.write_eeprom(para_idx*4 + 130, para & 0xFF)
        self.write_eeprom(para_idx*4 + 131, (para >> 8) & 0xFF)
        self.write_eeprom(para_idx*4 + 132, (para >> 16) & 0xFF)
        self.write_eeprom(para_idx*4 + 133, (para >> 24) & 0xFF)

    def get_eeprom_para(self, para_idx):
        assert para_idx < 32
        para = 0
        para = para | (self.read_eeprom(para_idx*4 + 130) << 0)
        para = para | (self.read_eeprom(para_idx*4 + 131) << 8)
        para = para | (self.read_eeprom(para_idx*4 + 132) << 16)
        para = para | (self.read_eeprom(para_idx*4 + 133) << 24)
        para = struct.pack('I',para)
        para = struct.unpack('i',para)[0]
        return para

    def read_eeprom(self, addr):
        module_id = 0x20
        dev_addr = 0x52
        self.write_regs([[module_id, 0x040, 0x0A]])
        self.write_regs([[module_id, 0x020, 0xD0]])
        self.write_regs([[module_id, 0x108, 0x100 | (dev_addr<<1)]])
        self.write_regs([[module_id, 0x108, 0x200 | addr]])
        self.write_regs([[module_id, 0x100, 0x0D]])
        time.sleep(0.001)
        self.write_regs([[module_id, 0x040, 0x0A]])
        self.write_regs([[module_id, 0x020, 0xD0]])
        self.write_regs([[module_id, 0x108, 0x100 | (dev_addr<<1) | 0x01]])
        self.write_regs([[module_id, 0x108, 0x200 | 0]])
        self.write_regs([[module_id, 0x100, 0x0D]])
        time.sleep(0.001)
        return self.read_regs([[module_id, 0x10C, 0x00]])[-1]&0xFF
    
    def _write_clock(self, addr, data):
        module_id = 0x20
        dev_addr = 0x60
        data = data & 0xFF
        self.write_regs([[module_id, 0x040, 0x0A]])
        self.write_regs([[module_id, 0x020, 0xD0]])
        self.write_regs([[module_id, 0x108, 0x100 | (dev_addr<<1)]])
        self.write_regs([[module_id, 0x108, (addr >> 8) & 0xFF]])
        self.write_regs([[module_id, 0x108, addr & 0xFF]])
        self.write_regs([[module_id, 0x108, 0x200 | data]])
        self.write_regs([[module_id, 0x100, 0x0D]])
        time.sleep(0.01)

    def _read_clock(self, addr):
        module_id = 0x20
        dev_addr = 0x60
        self.write_regs([[module_id, 0x040, 0x0A]])
        self.write_regs([[module_id, 0x020, 0xD0]])
        self.write_regs([[module_id, 0x108, 0x100 | (dev_addr<<1)]])
        self.write_regs([[module_id, 0x108, (addr >> 8) & 0xFF]])
        self.write_regs([[module_id, 0x108, addr & 0xFF]])
        self.write_regs([[module_id, 0x108, 0x100 | (dev_addr<<1) | 0x01]])
        self.write_regs([[module_id, 0x108, 0x200 | 1]])
        self.write_regs([[module_id, 0x100, 0x0D]])
        time.sleep(0.01)
        return self.read_regs([[module_id, 0x10C, 0x00]])
    
    def _set_mac(self, board_num):
        assert board_num < 65535
        self.clear_udp_buf()
        sta  = self._write_eeprom(0x0C, board_num)
        sta |= self._write_eeprom(0x0D, board_num >> 8)
        sta |= self._write_eeprom(0x0E, 0x70)
        sta |= self._write_eeprom(0x0F, 0x77)
        if sta==0:
            self.log.warning('board mac address is set to: 0x000A7770{:04X}'.format(board_num))
        else:
            self.log.critical('set mac failed')

    def _check_ip(self, ip_strs, netmask_strs, gateway_strs):
        # print('ip:{0}, netmask:{1}, gateway:{2}'.format(ip_strs, netmask_strs, gateway_strs))
        assert len(ip_strs)      == 4, len(ip_strs)     
        assert len(netmask_strs) == 4, len(netmask_strs)
        assert len(gateway_strs) == 4, len(gateway_strs)
        assert 0 < int(ip_strs[0])<255, int(ip_strs[0])
        assert 0 <=int(ip_strs[1])<255, int(ip_strs[1])
        assert 0 <=int(ip_strs[2])<255, int(ip_strs[2])
        assert 0 < int(ip_strs[3])<255, int(ip_strs[3])
        assert 0 < int(gateway_strs[0])<255, int(gateway_strs[0])
        assert 0 <=int(gateway_strs[1])<255, int(gateway_strs[1])
        assert 0 <=int(gateway_strs[2])<255, int(gateway_strs[2])
        assert 0 < int(gateway_strs[3])<255, int(gateway_strs[3])
        if int(ip_strs[0]) == 10:
            assert int(netmask_strs[0]) == 255, int(netmask_strs[0])
            assert int(netmask_strs[3]) == 0  , int(netmask_strs[3]) 
            if int(netmask_strs[2]) == 255:
                assert int(netmask_strs[1]) == 255, int(netmask_strs[1])
            else:
                assert int(netmask_strs[1]) == 0, int(netmask_strs[1])
                assert int(netmask_strs[2]) == 0, int(netmask_strs[2])
            assert gateway_strs[0] == ip_strs[0], '{},{}'.format(gateway_strs[0], ip_strs[0])
        if int(ip_strs[0]) == 192:
            assert int(ip_strs[1])      == 168    , int(ip_strs[1])     
            assert int(netmask_strs[0]) == 255    , int(netmask_strs[0])
            assert int(netmask_strs[1]) == 255    , int(netmask_strs[1])
            assert int(netmask_strs[3]) == 0      , int(netmask_strs[3])
            assert int(netmask_strs[2]) in [0,255], int(netmask_strs[2])
            assert gateway_strs[0] == ip_strs[0]  , '{},{}'.format(gateway_strs[0], ip_strs[0])
            assert gateway_strs[1] == ip_strs[1]  , '{},{}'.format(gateway_strs[1], ip_strs[1])
        if int(ip_strs[0]) == 172:
            assert int(ip_strs[1]) in range(16,31), int(ip_strs[1])
            assert int(netmask_strs[0]) == 255    , int(netmask_strs[0])
            assert int(netmask_strs[1]) == 255    , int(netmask_strs[1])
            assert int(netmask_strs[3]) == 0      , int(netmask_strs[3])
            assert int(netmask_strs[2]) in [0,255], int(netmask_strs[2])
            assert gateway_strs[0] == ip_strs[0]  , '{},{}'.format(gateway_strs[0], ip_strs[0])
            assert gateway_strs[1] == ip_strs[1]  , '{},{}'.format(gateway_strs[1], ip_strs[1])
        return True
    def set_network(self, ip, gateway, mask):
        self.clear_udp_buf()
        ip_strs = ip.strip().split('.')
        gateway_strs = gateway.strip().split('.')
        mask_strs = mask.strip().split('.')
        self._check_ip(ip_strs, mask_strs, gateway_strs)
        strs = ip_strs
        sta1 = [self._write_eeprom(i, int(strs[-i-1])) for i in range(4)]
        ipint = int(strs[3]) | (int(strs[2]) << 8) | (int(strs[1]) << 16) | (int(strs[0]) << 24)

        strs = gateway_strs
        sta2 = [self._write_eeprom(i+8, int(strs[-i-1])) for i in range(4)]
        gatewayint = int(strs[3]) | (int(strs[2]) << 8) | (int(strs[1]) << 16) | (int(strs[0]) << 24)
        
        strs = mask_strs
        sta3 = [self._write_eeprom(i+4, int(strs[-i-1])) for i in range(4)]
        maskint = int(strs[3]) | (int(strs[2]) << 8) | (int(strs[1]) << 16) | (int(strs[0]) << 24)

        sta = [0,0,0,0]
        if sta==sta1==sta2==sta3:
            self.write_regs([[0x50, 0x28, gatewayint]])
            self.write_regs([[0x50, 0x24, maskint]])
            self.write_regs([[0x50, 0x20, ipint]], need_return=False)
            self.log.critical('gateway set to:{0}'.format(gateway))
            self.log.critical('subnet mask set to:{0}'.format(mask))
            self.log.critical('ip set to:{0}, please reconnect device'.format(ip))
        else:
            self.log.critical(f'配置出现错误：请不要重启设备，直接尝试重新配置')
        
#%%
if __name__ == '__main__':
    ip = '192.168.1.44'
    raw_board = board()
    raw_board.connect(ip)

    # raw_board.start_ddr_read(1, 0, 4096)
    
    # write_ram_data(raw_board)
    # for i in range(1000):
    #     _ts1 = time.time()
    #     print(i)
    #     # ddr_read_test(raw_board)
    #     raw_board.ddr_self_test()
    #     raw_board.ram_self_test()
    #     # ddr_read_test(raw_board)
    #     _ts2 = time.time()
    #     print('t total:{0}'.format(_ts2 - _ts1))
           
    

# %%
