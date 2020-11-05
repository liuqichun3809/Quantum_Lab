#   FileName:AWGboard.py
#   Author:
#   E-mail:
#   All right reserved.
#   Modified: 2019.2.18
#   Description:The class of AWG
import os
import socket
import time

import numpy as np

from . import AWGBoardDefines
from . import mf_board as RAWBoard
import struct

class AWGBoard(RAWBoard.board):
    def __init__(self):
        super().__init__(dev_type = 'AWG')
        # Initialize core AWG parameters
        self.board_def = AWGBoardDefines.AWGBoardDefines()
        self.has_ddr = True
        self.awg_base_addr = 0x00000000
        self.awg_channel_space = 128 << 20 # 每通道的波形存储空间 128MB
        self.channel_count = 4
        self.frequency = 2e9
        self.sample_per_clock = 8
        self.isTrigSource = 0
        self.wave_is_unsigned = True
        self.mark_is_in_wave = False
        self.awgTrigDelayOffset = 0
        self.reg_id1 = 0x70
        self.reg_id2 = 0x71
        self.spi_id = 0x10
        self.max_cmd_cnt = 1 << 13
        self.sequence = []
        self.module_id_map = [0x10,0x10,0x11,0x11]
        self.ch_map = [0,1,0,1]
        # 电压预留系数， 0.1倍的预留空间，防止用户设置过大的偏置时，波形输出出现截止的情况
        self.coe = [1.1] * self.channel_count
        # DAC增益系数，用于多通道之间的一致性输出校准
        self.channel_gain = [1] * self.channel_count
        # 放大器增益系数，用于多通道之间的一致性输出校准
        self.diffampgain = [1] * self.channel_count
        # 该参数是出厂时的校准值，使AWG在32768码值时整体AWG输出电压为0V（DAC输出为满伏电压的一半）
        self._calibrated_offset = [0] * self.channel_count
        # 该参数是用户设置的偏置电压，该值使AWG输出为用户指定的电压值
        self.offset_volt = [0] * self.channel_count
        # 默认0电平码值
        self.zerocode = [32767] * self.channel_count
        self.amp_gain = [32767]  * self.channel_count
        # 每个通道对应的指令集执行的次数
        self.loopcnt = [60000] * self.channel_count
        # 每个通道是否在上一条指令执行后保持输出，默认不保持
        self.holdoutput = [0] * self.channel_count
        # wave length is the maximum data samples for each channel
        self.max_sample_cnt = 200000
        # 电压范围是负载以50欧匹配时看到的最大电压值
        self.voltrange = [1.0] * self.channel_count
        # 命令集
        self.commands = [None] * self.channel_count
        # 波形集
        self.waves = [None] * self.channel_count
        self.bank_dic = {'awg': [self.board_def.CHIP_AWG_1,
                                 self.board_def.CHIP_AWG_1,
                                 self.board_def.CHIP_AWG_2,
                                 self.board_def.CHIP_AWG_2],
                         'dac': [self.board_def.CHIP_9136_1,
                                 self.board_def.CHIP_9136_1,
                                 self.board_def.CHIP_9136_2,
                                 self.board_def.CHIP_9136_2]
                         }
        # print(f'dev_type is: {self.dev_type}')

    def write_spi_reg(self, spi_dev, offset, data, need_return = True):
        """[write data to spi regs]
        
        Arguments:
            spi_dev {[u8]} -- [spi module to be selected]
            offset {[u16]} -- [reg address to be write]
        
        Keyword Arguments:
            need_return {bool} -- [description] (default: {True})
        """
        self.write_regs([[self.spi_id, (spi_dev<<12)|offset, data]])
        # self.write_regs(3, [[data,spi_dev*6+2],[offset | 0x0000, spi_dev*6+0]])
    
    def read_spi_reg(self, spi_dev, offset, need_return = True):
        """[read data from spi regs]
        
        Arguments:
            spi_dev {[u8]} -- [spi module to be selected]
            offset {[u16]} -- [reg address to be write]
        
        Keyword Arguments:
            need_return {bool} -- [description] (default: {True})
        """
        return self.read_regs([[self.spi_id, (spi_dev<<12)|offset, 0]])[-1]

    def Write_Reg(self, bank, addr, data):
        """
        :param bank: 寄存器对象所属的BANK（设备或模块），4字节
        :param addr: 偏移地址，4字节
        :param data: 待写入数据，4字节
        :return: 4字节，写入是否成功，此处的成功是指TCP/IP协议的成功，也可以等效为数据写入成功

        :notes::

            这条命令下，AWG对象返回8字节数据，4字节表示状态，4字节表示数据

        """
        # if bank == 0: ## write cpu
        #    self.write_regs(0, [[data,addr]])
        #    return 0
        assert bank in [1,2,4,5]
        if bank == 1: ## write dac 1 spi 
           self.write_spi_reg(1, addr, data)
           return 0

        if bank == 2: ## write dac 2 spi
           self.write_spi_reg(2, addr, data)
           return 0
        
        if bank == 4: ## write awg 1 reg
           self.write_regs([[self.reg_id1, addr, data]])
           return 0
        
        if bank == 5: ## write awg 2 reg
           self.write_regs([[self.reg_id2, addr, data]])
           return 0

    def Read_Reg(self, bank, addr, data=0):
        """
        :param bank: 寄存器对象所属的BANK（设备或模块），4字节
        :param addr: 偏移地址，4字节
        :param data: 待写入数据，4字节
        :return: 4字节，读取是否成功，如果成功，返回读取的数据，否则，返回错误状态

        """
        # if bank == 0: ## write cpu
        #    return self.read_regs(0, [[data,addr]])[0]
        assert bank in [1,2,4,5]
        if bank == 1: ## write dac 1 spi 
           return self.read_spi_reg(1, addr, data)

        if bank == 2: ## write dac 2 spi
           return self.read_spi_reg(2, addr, data)
        
        if bank == 4: ## write awg 1 reg
           _ret = self.read_regs([[self.reg_id1, addr, 0]])
           return _ret[-1]
        
        if bank == 5: ## write awg 2 reg
           _ret = self.read_regs([[self.reg_id2, addr, 0]])
           return _ret[-1]
    
    # def Write_RAM(self, module_id, bank, start_addr, data, length):
    #     """
    #     :param module_id: 数据对象所属的模块，1字节
    #     :param bank: 数据对象所属的BANK（设备或模块），4字节
    #     :param start_addr: 写入存储区的起始地址
    #     :param data: 写入存储区的数据,数据是byts类型的list
    #     :param length: 写入存储区的数据长度
    #     :return: 写入成功或失败的错误状态
    #     """
        
    #     self.write_ram(module_id, bank, start_addr, data)
    #     return 0
    # 以下是常用AWG方法

    def setAWG_ID(self, dev_id):
        """
        设置AWG的ID标识
        :return:  None
        """
        self.dev_id = dev_id

    # 以下是常用AWG方法
    def set_channel_gain(self, channel, gain=1.0):
        """
        设置AWG通道的增益
        :param channel: AWG 通道 [1,2,3,4]
        :param gain:增益系数，取值要小于等于1
        :return:  None
        """
        assert gain <= 1.0
        self.channel_gain[channel - 1] = gain

    def _commit_para(self, channel):
        """
        提交AWG的配置参数
        :param self:
        :param channel: AWG 通道 [1,2,3,4]
        :return:  None，网络通信失败表示命令设置失败
        """

        self._channel_check(channel)
        self._SetZeroCode()
        bank = self.bank_dic['awg'][channel - 1]
        sub_ch = (((channel - 1) & 0x01) << 3)
        reg_low = self.zerocode[channel - 1] | (self.amp_gain[channel - 1] << 16)
        reg_low = reg_low | 1 if self.mark_is_in_wave else reg_low
        reg_high = self.loopcnt[channel - 1]
        addr = self.board_def.REG_CNFG_REG0 + sub_ch
        self.Write_Reg(bank, addr, reg_low)
        addr = addr + 4
        self.Write_Reg(bank, addr, reg_high)

    def SetLoop(self, channel, loopcnt):
        """
        :param self: AWG对象
        :param loopcnt: 通道ch波形输出循环次数，两字节
        :param channel: AWG 通道值（1，2，3，4）
        :return: None，网络通信失败表示命令设置失败
        """

        self._channel_check(channel)
        self.loopcnt[channel - 1] = loopcnt
        self._commit_para(channel)

    def SetMarkMode(self, mark_is_in_wave):
        """
        :param self: AWG对象
        :param mark_is_in_wave: mark输出模式，True，波形数据的最低位为mark标识，False：波形输出时，mark即有效
        """

        self.mark_is_in_wave = mark_is_in_wave
        for channel in range(1,5):
            self._commit_para(channel)

    def SetAmpGain(self, channel, amp_gain):
        """
        :param self: AWG对象
        :param amp_gain: 通道ch波形输出增益系数，范围[-1,1]
        :param channel: AWG 通道值（1，2，3，4）
        :return: None，网络通信失败表示命令设置失败
        """
        assert -1 <= amp_gain <= 1
        self._channel_check(channel)
        _b = struct.pack('<h', int(amp_gain*32767))
        _hex = struct.unpack('<H', _b)[0]
        self.amp_gain[channel - 1] = _hex
        self._commit_para(channel)
    
    def _SetZeroCode(self):
        if self.wave_is_unsigned:
            self.zerocode = [32768]*self.channel_count
        else:
            self.zerocode = [0]*self.channel_count

    def Start(self, channel):
        """
        :param self: AWG对象
        :param channel: 通道输出使能[1,2,3,4,12, 34] 12时同时使能1、2通道，34时同时使能3、4通道
        :return: None，网络通信失败表示命令设置失败
        :notes::
        """

        assert channel in [1, 2, 3, 4, 12, 34]
        # self._channel_check(channel)
        if channel == 12:
            _channel = 0x03
            _bank = self.bank_dic['awg'][0]
        elif channel == 34:
            _bank = self.bank_dic['awg'][2]
            _channel = 0x03
        else:
            _channel = 1 << ((channel - 1) & 0x01)
            _bank = self.bank_dic['awg'][channel - 1]
        self.Write_Reg(_bank, self.board_def.REG_CTRL_REG, _channel)

    def Stop(self, channel):
        """
        :param self: AWG对象
        :param channel: 通道输出禁止[1,2,3,4]
        :return: None，网络通信失败表示命令设置失败
        :notes::
        """
        assert channel in [1, 2, 3, 4]
        self._channel_check(channel)
        _channel = 16 << ((channel - 1) & 0x01)
        _bank = self.bank_dic['awg'][channel - 1]
        self.Write_Reg(_bank, self.board_def.REG_CTRL_REG, _channel)

    @staticmethod
    def _channel_check(channel):
        """
        :param channel: channel to be checked
        :return:
        """
        assert channel in [1, 2, 3, 4]

    def _SetDACMaxVolt(self, channel, volt):
        """

        该函数用于设置芯片的最大输出电压

        :param channel: AWG 通道（1，2，3，4）
        :param volt: 最大电压值
        :return:
        :notes::
            满电流值计算公式：
            IOUTFS = 20.48 + (DACFSC_x × 13.1 mA)/2^(10 ? 1)
        """
        assert volt <= 1.351
        assert volt >= 0.696
        cur = volt / 0.05
        code = (cur - 20.48) * 1024 / 13.1
        code = int(code) & 0x3FF
        self._SetDACFullScale(channel, code)

    def _SetDACFullScale(self, channel, data):
        """

        该函数根据输入的码值写入芯片

        :param self: AWG对象
        :param channel: AWG 通道 [1,2,3,4]
        :param data: 增益值，该值是12位二进制补码形式的增益数据
        :return:

        """
        self._channel_check(channel)
        _bank = self.bank_dic['dac'][channel - 1]
        addr = 0x40 + 4 * ((channel-1)&0x01)
        self.Write_Reg(_bank, addr+1, data & 0xFF)  # 写入满电流值低字节
        self.Write_Reg(_bank, addr, (data >> 8) & 0x03)  # 写入满电流值高字节

    def SetOutputHold(self, channel, is_hold):
        """
        :param self: AWG对象
        :param channel: 通道值（1，2，3，4）
        :param is_hold: 对应通道的输出是否需要保持, 1,保持，0，不保持
        :return: None，网络通信失败表示命令设置失败

        :notes::

            保持的时候波形输出会保持为最后的8个采样点
            的值不断的重复输出（此处要注意这个特性）
            该特性可以实现很少的码值输出很长的台阶波形

            在不保持时，波形输出完成后会回到设定的默认电压值
        """

        self._channel_check(channel)
        self.holdoutput[channel - 1] = is_hold
        self._commit_para(channel)

    def SetOffsetVolt(self, channel, offset_volt):
        """

        设置某个通道的偏置电压，该功能对当前通道的波形做偏置设置
        由于是通过DA码值来实现的，因此会消耗DA的有效码值范围

        :param self: AWG对象
        :param channel: 通道值（1，2，3，4）
        :param offset_volt: 对应的偏置电压值
        :return: None，网络通信失败表示命令设置失败
        """

        self._channel_check(channel)
        assert abs(offset_volt) < 0.1  # 电压偏移不能超过 ±0.1V
        volt = offset_volt
        if abs(volt) > self.voltrange[channel - 1]:
            print('偏移电压设置值{0}超过AWG范围[{1}-{2}], 电压值将会设为0'.format(volt,-self.voltrange[channel-1], self.voltrange[channel-1]))
            volt = 0

        code = int(volt * 65535 / self.coe[channel - 1] / (2 * self.voltrange[channel - 1]))
        self._SetDacOffset(channel, code)
        self.offset_volt[channel - 1] = offset_volt

    def _SetCalibratedOffsetCode(self, channel, offset_code):
        """

        该函数设置的偏置值用于校准仪器在默认连接时的0电平码值

        :param channel: AWG通道[1，2，3，4]
        :param offset_code: 偏置码值
        :return:
        """
        self._channel_check(channel)
        self._calibrated_offset[channel - 1] = offset_code

    def _SetDacOffset(self, channel, offset_code):
        """

        :param self: AWG对象
        :param channel: 通道值（1，2，3，4）
        :param offset_code: 对应的DA通道的offset值，精度到1个LSB
        :return: None，网络通信失败表示命令设置失败
        """

        self._channel_check(channel)
        page = ((channel - 1) & 0x01) + 1
        temp1 = (offset_code + self._calibrated_offset[channel - 1] >> 0) & 0xFF
        temp2 = (offset_code + self._calibrated_offset[channel - 1] >> 8) & 0xFF

        _bank = self.bank_dic['dac'][channel - 1]
        self.Write_Reg(_bank, 0x008, page)  # 分页
        self.Write_Reg(_bank, 0x135, 1)  # 使能offset
        self.Write_Reg(_bank, 0x136, temp1)  # LSB [7:0]
        self.Write_Reg(_bank, 0x137, temp2)  # LSB [15:8]
        self.Write_Reg(_bank, 0x13A, 0)  # SIXTEEN [4:0]

    def _AWGChannelSelect(self, channel, cmd_or_wave):
        """

        :param self: AWG对象
        :param channel: 通道值（1，2，3，4）
        :param cmd_or_wave: 命令通道（0）或波形数据通道（1）
        :return: None，网络通信失败表示命令设置失败
        """

        self._channel_check(channel)
        assert cmd_or_wave in [0,1]
        _bank = self.bank_dic['awg'][channel - 1]
        pos = ((channel-1) & 0x01) + (cmd_or_wave << 2)
        self.Write_Reg(_bank, self.board_def.REG_CNFG_REG4, 1 << pos)


    @staticmethod
    def _format_data(data, unsigned=True):
        """
        :param data: 准备格式化的数据
        :return: 格式化后的数据
        :notes::
            输入的数据是无符号short类型数据，转换成网络接口接受的字节流
        """
        if unsigned:
            fmt = "{0:d}H".format(len(data))
        else:
            fmt = "{0:d}h".format(len(data))
        packet = struct.pack(fmt, *data)
        return packet

    def _WriteWaveCommands(self, channel, commands):
        """
        :param self: AWG对象
        :param channel: 通道值（1，2，3，4）
        :param commands: 波形输出控制指令数据
        :return: None，网络通信失败表示命令设置失败
        """
        self._channel_check(channel)
        self._AWGChannelSelect(channel, 0)  # 0表示命令
        startaddr = 0  # 序列的内存起始地址，单位是字节。
        packet = self._format_data(commands)
        # _bank = self.bank_dic['awg'][channel - 1]
        # _ch_map = [2,3,2,3]
        _module_id = self.module_id_map[channel-1]
        _bank = 1 << (self.ch_map[channel-1]+2)
        self.write_ram(_module_id, _bank, startaddr, packet)
        # # TODO, PCIE 时还需要修改
        # offset = 0
        # unit_size = 1024
        # cycle_cnt = int(len(packet) / unit_size)  #
        # for _ in range(cycle_cnt):
        #     self.Write_RAM(_module_id, _bank, startaddr, packet[offset:offset + unit_size], unit_size)
        #     startaddr += (unit_size >> 2)
        #     offset += unit_size
        # if len(packet) & (unit_size - 1) > 0:
        #     self.Write_RAM(_module_id, _bank, startaddr, packet[offset:], len(packet) & (unit_size - 1))

    def _WriteWaveData(self, channel, wave):
        """
        :param self: AWG对象
        :param channel: 通道值（1，2，3，4）
        :param wave: 波形输出数据
        :return: None，网络通信失败表示命令设置失败
        """

        self._channel_check(channel)
        if self.wave_is_unsigned:
            assert max(wave) < 65536  # 码值异常，大于上限
            assert min(wave) >= 0  # 码值异常，小于下限
        else:
            assert max(wave) < 32769, max(wave)  # 码值异常，大于上限
            assert min(wave) > -32769, min(wave)  # 码值异常，小于下限
        self._AWGChannelSelect(channel, 1)  # 1表示波形数据
        startaddr = 0  # 波形数据的内存起始地址，单位是字节。
        pkt_unit = 512
        pad_cnt = (pkt_unit - len(wave) & (pkt_unit-1)) & (pkt_unit-1)
        temp_wave = wave + [self.zerocode[channel - 1]] * pad_cnt

        packet = self._format_data(temp_wave, self.wave_is_unsigned)
        # _bank = self.bank_dic['awg'][channel - 1]
        # _ch_map = [0,1,0,1]
        _bank = 1 << (self.ch_map[channel-1])
        _module_id = self.module_id_map[channel-1]
        if self.has_ddr:
            self.write_ddr(1, startaddr+self.awg_base_addr, packet)
        else:
            self.write_ram(_module_id, _bank, startaddr, packet)
        # # TODO, PCIE 时还需要修改
        # offset = 0
        # unit_size = 1024
        # cycle_cnt = int(len(packet) / unit_size)  #
        # for _ in range(cycle_cnt):
        #     self.Write_RAM(_module_id, _bank, startaddr, packet[offset:offset + unit_size], unit_size)
        #     startaddr += (unit_size >> 2)
        #     offset += unit_size
        # if len(packet) & (unit_size - 1) > 0:
        #     self.Write_RAM(_module_id, _bank, startaddr, packet[offset:], len(packet) & (unit_size - 1))

    def load_data_to_ram(self, channel):
        _loop = self.loopcnt[channel-1]
        # pad_cnt = (4096-(len(self.waves[channel-1])&0xFFF))&0xFFF
        # _d = self.waves[channel-1]+[self.zerocode[channel-1]]*pad_cnt
        # _d = self._format_data(_d, self.wave_is_unsigned)
        # self.write_ddr(1, self.awg_base_addr, _d)
        _len = (len(self.waves[channel-1]) + 511) >> 9
        addr = self.awg_base_addr >> 10
        cmd = [addr & 0xFFFF,0x0f00 | (addr >> 16), _len, self.board_def.AWG_CMD_READ2RAM]
        cmd += [0,1,0,self.board_def.AWG_CMD_NULL_CNT | 0x8000]
        self._WriteWaveCommands(channel, cmd)
        self.SetLoop(channel,1)
        self.Start(channel)
        time.sleep(0.001)
        self.SetLoop(channel, _loop)

    def _gen_ddr_rd_block_size(self, length):
        ddr_block_size = 0x0F
        if length & 0x3FFF == 0:
            ddr_block_size = 0xFF
        elif length & 0x1FFF == 0:
            ddr_block_size = 0x7F
        elif length & 0xFFF == 0:
            ddr_block_size = 0x3F
        elif length & 0x7FF == 0:
            ddr_block_size = 0x1F
        return ddr_block_size

    def gen_wave_control_auto(self, channel, wave_size, wave_type, wave_cnt, repeat_cnt, wave_addr=0, delay=0):
        """[生成特定功能的波形控制输出，ddr中的相同长度的短波形重复输出]

        波形文件大小为1024字节的整数倍，每个波形的长度相等
        两个波形间的切换时间，1us/kB，波形长度增加，切换时间会加长, 波形切换时不响应外部触发信号
        波形的触发重复间隔为波形时间长度+20ns, 例如，波形长度为1us时，该重复触发输出该波形的最小触发间隔为1us+20ns

        波形输出描述，假定有N(N<=50000)个波形，每个波形：
        wave_addr:第一个波形在DDR存储的起始地址,单位为字节，1024的整数倍
        wave_size:每个波形的文件大小,单位为字节，1024的整数倍, 最大200kB
        wave_type:波形的输出类型，触发和延时类型
        wave_cnt:波形的个数， 波形个数*波形大小 不超过512MB
        repeat_cnt:每个波形输出重复次数，最大50000次
        delay:波形是计时输出类型时，波形输出前的延时值，单位为秒 最大250us
        """   
        assert (wave_addr & 0x3FF) == 0
        assert (wave_size & 0x3FF) == 0
        assert wave_type in ('trig', 'delay')
        assert wave_size <= (200<<10)
        assert wave_cnt*wave_size + wave_addr < (512<<20), 'wave space error'
        assert repeat_cnt <= 50000
        assert delay <= 250e-5
        wave_addr = wave_addr + self.awg_base_addr
        # read data from ddr to ram
        # trig loop
        # delay loop    
        # 波形控制由以下几条指令组成
        # 1. read ddr data to ram, address is wave_addr
        # 2. wait null cnt for ddr data ready
        # 3. loop1 start
        # 4. read ddr data to ram, address auto add
        # 5. wait null cnt 
        # 6. loop2 start
        # 7. trig output
        # 8. loop2 end
        # 9. loop1 end
        # 10. null cnt and stop
        ddr_arlen = self._gen_ddr_rd_block_size(wave_size) << 8
        auto_flag = 0x80
        stop_flag = 0x8000
        addr1 = (wave_addr>>10) & 0xFFFF
        addr2 = (wave_addr>>26)
        len1  = (wave_size>>10) & 0xFFFF
        wait_cnt = len1*2500*16
        # wait_cnt = int(1e6) #wait for 4ms
        delay_cnt = int(delay/(self.sample_per_clock/self.frequency))
        cmd = []
        cmd.extend([addr1,addr2|ddr_arlen, len1, self.board_def.AWG_CMD_READ2RAM])
        cmd.extend([wait_cnt&0xFFFF, wait_cnt>>16, 0, self.board_def.AWG_CMD_NULL_CNT])
        cmd.extend([0, 0, wave_cnt, self.board_def.AWG_CMD_NULL_LOOP_S])
        cmd.extend([addr1,addr2|ddr_arlen|auto_flag, len1, self.board_def.AWG_CMD_READ2RAM])
        # cmd.extend([len1,ddr_arlen|auto_flag, len1, self.board_def.AWG_CMD_READ2RAM])
        cmd.extend([wait_cnt&0xFFFF, wait_cnt>>16, 0, self.board_def.AWG_CMD_NULL_CNT])
        cmd.extend([0, 0, repeat_cnt, self.board_def.AWG_CMD_NULL_LOOP_S|0x100])
        if wave_type == 'trig':
            cmd.extend([0, int(wave_size/(self.sample_per_clock*2)), 0, self.board_def.AWG_CMD_TRIG])
        else:
            cmd.extend([0, int(wave_size/(self.sample_per_clock*2)), delay_cnt, self.board_def.AWG_CMD_COUNT])
        cmd.extend([0, 0, 5, self.board_def.AWG_CMD_NULL_LOOP_E|0x100])
        cmd.extend([0, 0, 2, self.board_def.AWG_CMD_NULL_LOOP_E])
        cmd.extend([2, 0, 0, self.board_def.AWG_CMD_NULL_CNT|stop_flag])
        self._WriteWaveCommands(channel, cmd)
        return cmd

    def gen_wave_control_from_sequence(self, wait_time=1e-3):
        """[生成特定功能的波形控制输出，短波形]

        波形文件大小为1024字节的整数倍，每个波形文件的大小小于等于200kB
        两个波形间的切换时间，1us/kB，波形长度增加，切换时间会加长, 波形切换时不响应外部触发信号
        同一个波形的触发重复间隔为波形时间长度+20ns, 例如，波形长度为1us时，该重复触发输出该波形的最小触发间隔为1us+20ns

        sequence单元：字典类型
        {
            'start_addrs':start_addrs, 
            'next_addrs':next_addrs,
            'wave_sizes':wave_sizes, 
            'wait':wait, 
            'goto':goto, 
            'repeat':repeat, 
            'delay':0
        }

        波形输出描述，假定有N(N<=500)个波形，第n个波形：
        An:波形在DDR存储的起始地址
        Ln:波形的长度
        Tn:波形的输出类型
        Rn:波形输出重复次数
        Dn:波形是计时输出类型时，波形输出前的延时值
        """   
        # 对每一个波形输出，用以下命令完成
        # 1. read data from ddr to ram
        # 2. wait null cnt
        # 3. 如果重复次数大于1, loop start
        # 4. wait_trig/wait_cnt
        # 5. 如果重复次数大于1, loop end
        # 6. 最后加入一个结束指令
        assert len(self.sequence) > 0, 'there is no sequence data'
        sequence = self.sequence
        auto_flag = 0x00 #不自动增加地址
        stop_flag = 0x8000
        ch_cnt = len(sequence[0]['start_addrs'])
        seq_dic = {i:[] for i in range(ch_cnt)}
        wait_cnt = int(wait_time/4e-9) # ADDA在一起时等待1ms，等待读取数据的时间500ns+1us/kB
        for s in sequence:
            delay = s['delay']
            assert 0 <= delay < 256e-6, 'delay time shuld less than 256 us'
            delay_cnt = int(np.ceil(delay/(self.sample_per_clock/self.frequency)))
            repeat = s['repeat']
            assert 0 <= repeat <= 50000 , 'max repeat count is 50000'
            for idx, wave_info in enumerate(zip(s['start_addrs'], s['wave_sizes'])):
                start_addr= wave_info[0] + self.awg_base_addr + self.awg_channel_space*(idx)
                wave_size = wave_info[1]
                cmd = seq_dic[idx]
                assert len(cmd)<(self.max_cmd_cnt*4), 'commands count {0} reached max size {1}'.format(len(cmd), self.max_cmd_cnt)
                rd_size = (wave_size+1023) & 0xFFC00 # wave read size is 1kB aligned
                ddr_arlen = self._gen_ddr_rd_block_size(rd_size) << 8 # get ddr read block size
                # print(f'start addr in cmd: {hex(start_addr)}')
                addr1 = (start_addr>>10) & 0xFFFF
                addr2 = (start_addr>>26)
                rd_len  = (rd_size>>10) & 0xFFFF #读取长度，单位为kB
                # 1. read data from ddr to ram 
                cmd.extend([addr1,addr2|ddr_arlen|auto_flag, rd_len, self.board_def.AWG_CMD_READ2RAM])
                # 2. wait null cnt
                cmd.extend([wait_cnt&0xFFFF, wait_cnt>>16, 0, self.board_def.AWG_CMD_NULL_CNT])
                # 3. 如果重复次数大于1, loop start
                if repeat > 1:
                    jump_addr = len(cmd) >> 2
                    cmd.extend([0, 0, repeat, self.board_def.AWG_CMD_NULL_LOOP_S|0x100])
                # 4. wait_trig/wait_cnt
                if s['wait'] == 'trig':
                    cmd.extend([0, int(np.ceil(wave_size/(self.sample_per_clock*2))), 0, self.board_def.AWG_CMD_TRIG])
                else:
                    cmd.extend([0, int(np.ceil(wave_size/(self.sample_per_clock*2))), delay_cnt, self.board_def.AWG_CMD_COUNT])
                # 5. 如果重复次数大于1, loop end
                if repeat > 1:
                    cmd.extend([0, 0, jump_addr, self.board_def.AWG_CMD_NULL_LOOP_E|0x100])
        # 6. 最后加入一个结束指令
        for key in seq_dic:
            seq_dic[key].extend([2, 0, 0, self.board_def.AWG_CMD_NULL_CNT|stop_flag])
        self.seq_dic = seq_dic
        
    def gen_wave_control_long(self, channel, wave_size, wave_type, wave_cnt, repeat_cnt, wave_addr=0, delay=0):
        """[生成特定功能的波形控制输出,输出长波形]
        
        波形数据在存储器中的存储方式(交叉存储)：
        CH1SP0,CH2SP0,CH1SP1,CH2SP1,...,CH1SPn,CH2SPn

        限制条件，波形长度为16384字节(16kB)的整数倍, 波形文件大小最大128MB
        最多可以同时输出两个通道，以下6种输出是合法的
        可以12通道输出，1通道输出
        可以34通道输出，3通道输出
        
        波形间最小间隔, 10us

        波形输出描述，假定有N个波形，第n个波形：
        An:波形在DDR存储的起始地址
        Ln:波形的长度
        Tn:波形的输出类型
        Rn:波形输出重复次数
        Dn:波形是计时输出类型时，波形输出前的延时值
        """   
        assert (wave_addr & 0x3FF) == 0
        assert (wave_size & 0x3FF) == 0
        assert wave_type in ('trig', 'delay')
        assert wave_size <= (200<<10)
        assert wave_cnt*wave_size + wave_addr < (512<<20), 'wave space error'
        assert repeat_cnt <= 50000
        assert delay <= 250e-6
        # read data from ddr to ram
        # trig loop
        # delay loop    
        # 波形控制由以下几条指令组成
        # 1. read ddr data to ram, address is wave_addr
        # 2. wait null cnt for ddr data ready
        # 3. loop1 start
        # 4. read ddr data to ram, address auto add
        # 5. wait null cnt 
        # 6. loop2 start
        # 7. trig output
        # 8. loop2 end
        # 9. loop1 end
        # 10. null cnt and stop
        ddr_arlen = self._gen_ddr_rd_block_size(wave_size) << 8
        auto_flag = 0x80
        stop_flag = 0x8000
        addr1 = (wave_addr>>10) & 0xFFFF
        addr2 = (wave_addr>>26)
        len1  = (wave_size>>10) & 0xFFFF
        wait_cnt = len1*2500
        delay_cnt = int(delay/(self.sample_per_clock/self.frequency))
        cmd = []
        cmd.extend([addr1,addr2|ddr_arlen, len1, self.board_def.AWG_CMD_READ2RAM])
        cmd.extend([wait_cnt&0xFFFF, wait_cnt>>16, 0, self.board_def.AWG_CMD_NULL_CNT])
        cmd.extend([0, 0, wave_cnt, self.board_def.AWG_CMD_NULL_LOOP_S])
        cmd.extend([addr1,addr2|ddr_arlen|auto_flag, len1, self.board_def.AWG_CMD_READ2RAM])
        # cmd.extend([len1,ddr_arlen|auto_flag, len1, self.board_def.AWG_CMD_READ2RAM])
        cmd.extend([wait_cnt&0xFFFF, wait_cnt>>16, 0, self.board_def.AWG_CMD_NULL_CNT])
        cmd.extend([0, 0, repeat_cnt, self.board_def.AWG_CMD_NULL_LOOP_S|0x100])
        if wave_type == 'trig':
            cmd.extend([0, int(wave_size/(self.sample_per_clock*2)), 0, self.board_def.AWG_CMD_TRIG])
        else:
            cmd.extend([0, int(wave_size/(self.sample_per_clock*2)), delay_cnt, self.board_def.AWG_CMD_COUNT])
        cmd.extend([0, 0, 5, self.board_def.AWG_CMD_NULL_LOOP_E|0x100])
        cmd.extend([0, 0, 2, self.board_def.AWG_CMD_NULL_LOOP_E])
        cmd.extend([2, 0, 0, self.board_def.AWG_CMD_NULL_CNT|stop_flag])
        self._WriteWaveCommands(channel, cmd)
        return cmd

    def gen_wave_control_single(self, wave_len, ):
        """[生成特定功能的波形控制输出,输出长波形]
        限制条件，波形长度为16384字节(16kB)的整数倍
        波形输出描述，假定有N个波形，每个波形的长度相同：
        L:波形的长度
        T:波形的输出类型
        R:每个波形输出重复次数
        D:波形是计时输出类型时，波形输出前的延时值
        """   
        pass
        # loop begin
        # read data from ddr to fifo
        # wait cnt
        # wait ddr count / wait ddr trig
        # loop end  



    @staticmethod
    def _get_volt(value):
        """
        返回满电流码值对应的电压值
        :param value: 满电流码值
        :return: 电压值
        """
        sign = value >> 9
        code = value & 0x1FF
        volts = (20.48 + ((code - (sign << 9)) * 13.1) / 1024) * 0.05
        return volts

    def gen_wave_unit(self, wave_data, wave_type='延时', start_time=0, mark=None):
        """[summary]

        Arguments:
            wave_data {[type]} -- [波形数据]

        Keyword Arguments:
            mark {[type]} -- [波形mark标识，表示波形数据中的某个点需要输出有效标识，该功能可让用户自主控制波形数据中的哪一部分输出mark标志] (default: {None})
            wave_type {str} -- [波形类型，支持触发，延时，连续3种类型] (default: {'延时'})
            start_time {int} -- [波形输出起始时间，单位：秒] (default: {0})

        Returns:
            [type] -- [生成描述一个波形的波形字典单元，返回字典类型的元组]
        """        
        assert wave_type in ['延时', 'delay', '触发', 'trig', '连续', 'continue']
        if self.mark_is_in_wave:
            assert mark is not None, "there isn't mark data"
            assert len(wave_data) == len(mark), 'mark data length shuld be same as wave data'
            assert max(mark) <= 1, max(mark)
            assert min(mark) <= 1, min(mark)
        return {'wave_data': wave_data, 'wave_type': wave_type, 'start_time': start_time, 'mark': mark}   


    def wave_compile(self, channel, waves_list, is_continue=False, false_data=False):
        """
        编译并合成多个波形，每个波形的类型，起始时间，波形数据均由用户提供

        :param is_continue: 是否要生成连续输出的波形，该值为真时，最终合成的波形是周期性连续不断输出，不需要等待触发信号
        :param channel: 编译的波形对应的AWG通道
        :param waves_list: 要合成的波形序列序列中每个单元应该包含:

            wave_list:  波形数据列表

            type_list: 每个要合成的波形的类型

            start_time_list: 波形输出起始时间，以第一条指令的对应触发为0时刻，所有波形的输出时间均相对最近的触发指令0时刻计算，
            所有的触发指令都会使计时清零，即触发指令充当了重新同步的功能

        :return: 波形类得到合成后的波形数据，相应的控制命令集

        :notes::

            这类波形的第一条一般都是触发类型的，配上其他的波形类型
            输出可以实现指定时间输出指定波形的功能，所有输出的参考
            时间是相对于最近一条触发指令的触发沿的

            每一条触发类型的波形都可以重新实现与输入触发信号的同步对齐
        """
        # TODO:首先对输入的波形序列做预处理，两段波形输出间隔过小(小于16ns)的，可以合并成一条波形（暂时没做, 只做了长度判断）

        # 修整后，每一条指令会完整的输出至少一段波形

        self._channel_check(channel)

        wave_list = []
        type_list = []
        start_time_list = []

        volt_factor = self.coe[channel - 1]  # self.voltrange[channel - 1][1] - self.voltrange[channel - 1][0]
        addr_step = int(np.log2(self.sample_per_clock))
        if self.wave_is_unsigned :
            _volt_offset = 1
        else:
            _volt_offset = 0
        for item in waves_list:
            # 电压到码值的转换，为了给偏置留余量，要求最大输出电压比给用户的电压多10%，对于vpp为2V的AWG，其最大电压输出其实能到2.2V
            a1 = np.asarray(item['wave_data'])
            a1 = a1.astype(np.float) * self.channel_gain[channel - 1]
            # print(a1)
            a1 = a1 / volt_factor

            if self.mark_is_in_wave:
                a1 = (a1 + _volt_offset) * 32767.5/2
                b1 = a1.astype(np.uint16) * 2
                c1 = b1 + np.asarray(item['mark'])
                a1 = c1
            else:
                a1 = (a1 + _volt_offset) * 32767.5

            if self.wave_is_unsigned :
                trans_wave = list(a1.astype(np.uint16))
            else:
                trans_wave = list(a1.astype(np.int16))

            wave_list.append(trans_wave)
            type_list.append(item['wave_type'])
            start_time_list.append(item['start_time'])

        cur_sample_point = 0
        wave = []
        command = []
        for idx, wave_type in enumerate(type_list):
            if wave_type in ['触发','trig'] :
                """触发类型的指令需要配一个延时参数，表示触发信号到达后，延时多少时间输出，
                触发指令可以看做重新同步指令，那么，一串的波形就可以通过触发指令分割成多个序列来处理
                所以，触发指令一定是当做第一条指令来处理，他的起始时刻重新归零计算，但是地址要相对已有波形最后一个点
                触发波形对应的命令有3个参数：延时计数，波形起始地址，输出长度
                """
                cmd_id = 0x4000
                cur_sample_point = 0
            elif wave_type in ['连续', 'continue']:
                cmd_id = 0x0000
                pass
            else: ## 延时输出
                cmd_id = 0x2000

            # 计算起始时间对应的采样点
            # print('波形长度',len(wave_list[idx]))
            assert len(wave_list[idx]) >= 32, 'every wave data should have sample points large than 31'
            sample_cnt = round(start_time_list[idx] * self.frequency)
            # 计算与上一个结束时间的采样点间隔，如果时间重叠
            delta_cnt = (sample_cnt - cur_sample_point)
            assert delta_cnt >= 0, 'time overlap'
            # 计算延时计数器的值
            delay_cnt = delta_cnt >> addr_step
            # 如果起始时间与计数器不对齐，通过波形点前面补齐
            pad_cnt = delta_cnt & (self.sample_per_clock-1)
            temp_wave = [self.zerocode[channel - 1]] * pad_cnt
            temp_wave = temp_wave + wave_list[idx]
            # 如果补齐后的结束时间与时钟周期不对齐，通过波形点后面补齐
            pad_cnt = (self.sample_per_clock - len(temp_wave) & (self.sample_per_clock-1)) & (self.sample_per_clock-1)
            temp_wave = temp_wave + [self.zerocode[channel - 1]] * pad_cnt

            # 生成起始地址，波形长度
            start_addr = len(wave) >> addr_step
            length = (len(temp_wave) >> addr_step)
            # 生成对应的命令
            # print(start_addr, length)
            assert start_addr + length <= (self.max_sample_cnt >> addr_step), 'generated waveform is to long'
            assert delay_cnt <= 65535, 'delay count is large than 260us'
            temp_cmd = [start_addr, length, delay_cnt, cmd_id]

            # 拼接命令集与波形集
            command = command + temp_cmd
            wave = wave + temp_wave
            cur_sample_point += (delay_cnt << addr_step) + len(temp_wave)

        # 最后一条命令要带停止标识，标识是最后一条命令
        if false_data:
            self.waves[channel - 1] = [i for i in range(len(wave))]
        else:
            self.waves[channel - 1] = list(wave)

        if len(command) == 4 and not is_continue:
            self.commands[channel - 1] = command * self.max_cmd_cnt
        else:
            command[-1] |= 0x8000
            self.commands[channel - 1] = list(command)
        if is_continue:
            self.commands[channel - 1] = [0, len(wave) >> addr_step, 0, 0] * self.max_cmd_cnt

        # 将编译的波形上传到AWG
        self._upload_data(channel)

    def write_wave_to_ddr(self, channel, start_addr, wave, mark=None):
        """[编译波形，根据起始地址，将编译后的数据写入ddr，
        每个AWG有4个独立的存储空间，start addr是相对于相应存储空间的偏移地址]

        Args:
            channel ([int]): [通道标识]
            wave ([np array]): [波形数据，归一化整数]
            start_addr ([int]): [起始偏移地址]
            mark ([np array]): [mark数组，如果不为None,长度需要和wave一样]
        Returns:
            [int]: [next_addr:next valid offset address for writing]
            [int]: [wave_size:wave size in bytes]
        """ 
        # 起始地址要考虑各通道的DDR空间， 波形数据要考虑补齐成1kB整数倍
        _start_addr = start_addr + self.awg_base_addr + self.awg_channel_space*(channel-1)
        wave_size = len(wave) << 1
        self._channel_check(channel)
        pad_cnt = (512-(len(wave)&511)) & 511
        wave = np.pad(wave, (0,pad_cnt), mode='constant')
        volt_factor = self.coe[channel - 1]  # self.voltrange[channel - 1][1] - self.voltrange[channel - 1][0]
        if self.wave_is_unsigned :
            _volt_offset = 1
        else:
            _volt_offset = 0
        a1 = wave * self.channel_gain[channel - 1]
        a1 = a1 / volt_factor
        # a1 = (a1 + _volt_offset) * 32767.5
        if self.mark_is_in_wave and mark is not None:
            assert len(mark) == len(wave)
            a1 = (a1 + _volt_offset) * 32767.5/2
            b1 = a1.astype(np.uint16) * 2
            c1 = b1 + mark
            a1 = c1
        else:
            a1 = (a1 + _volt_offset) * 32767.5
        
        if self.wave_is_unsigned :
            wave_data = a1.astype(np.uint16)
        else:
            wave_data = a1.astype(np.int16)
        
        # print(f'wave write to ddr: {hex(_start_addr)}')
        # 将编译的波形上传到DDR
        self.write_ddr(start_addr=_start_addr, data=wave_data.tobytes())
        # next addr 计算不能加上base addr
        next_addr = start_addr + (len(wave_data) << 1)
        return next_addr, wave_size

    def display_AWG(self):
        """
        :param self: AWG对象
        :return: 打印AWG信息
        """
        print('AWG ID: %s'%self.dev_id,' address: %s'%self.dev_ip)
        print('AWG sampling rate(GSPS): %.5f'%(self.frequency/1e9))
        print('AWG resolution: 16bit')
        print('AWG channel number: %s'%self.channel_count)
        for channel in range(self.channel_count):
            print('AWG channel '+str(channel+1)+' volt range: %s-%s V'%(-self.voltrange[channel],self.voltrange[channel]))
        s = [str(i) for i in self.offset_volt]
        print('offset volts for all channels(V): ' + ','.join(s))
        _default_code = []
        _default_code.append(round((self.Read_Reg(4, 0x80)>>16)/32767,4))
        _default_code.append(round((self.Read_Reg(4, 0x88)>>16)/32767,4))
        _default_code.append(round((self.Read_Reg(5, 0x80)>>16)/32767,4))
        _default_code.append(round((self.Read_Reg(5, 0x88)>>16)/32767,4))
        _mark_mode = []
        mark_map = {0:'wave independent', 1:'merge into wave'}
        _mark_mode.append(mark_map[self.Read_Reg(4, 0x80) & 0x01])
        _mark_mode.append(mark_map[self.Read_Reg(4, 0x88) & 0x01])
        _mark_mode.append(mark_map[self.Read_Reg(5, 0x80) & 0x01])
        _mark_mode.append(mark_map[self.Read_Reg(5, 0x88) & 0x01])
        _cur_loop = []
        _cur_loop.append(self.Read_Reg(4, 0x84))
        _cur_loop.append(self.Read_Reg(4, 0x8C))
        _cur_loop.append(self.Read_Reg(5, 0x84))
        _cur_loop.append(self.Read_Reg(5, 0x8C))
        _key = [i for i in range(16)]
        _status_map = dict(zip(_key, ['other']*len(_key)))
        _status_map[0] = 'idle'
        _status_map[2] = 'wait trigger'
        _status_map[15] = 'wait trigger'
        _status_map[8] = 'wait counter'
        _status_map[7] = 'output wave'
        _status_map[9] = 'wait ddr data'
        _status_map[10] = 'read ddr to ram'
        _status_map[11] = 'read ddr to fifo'
        _cur_sta = []
        _cur_sta.append(_status_map[(self.Read_Reg(4, 0x100) >> 1) & 0xF])
        _cur_sta.append(_status_map[(self.Read_Reg(4, 0x104) >> 1) & 0xF])
        _cur_sta.append(_status_map[(self.Read_Reg(5, 0x100) >> 1) & 0xF])
        _cur_sta.append(_status_map[(self.Read_Reg(5, 0x104) >> 1) & 0xF])
        ch = 1
        for _loop, _sta, _d, _m in zip(_cur_loop, _cur_sta, _default_code, _mark_mode):
            print('AWG channel %d: loop count: %8d, wave multiplication:%.4f, status: %s, mark mode: %s'%(ch, _loop, _d, _sta, _m))
            ch += 1
    def set_awg_para(self):
        self.write_eeprom(128, 0xDA)
        self.write_eeprom(129, 0x00)
        for idx,d in enumerate(self._calibrated_offset):
            self.set_eeprom_para(idx, d)
        for idx,d1 in enumerate(self.diffampgain):
            d = int(d1 * 65536)
            self.set_eeprom_para(idx+4, d)
        self.write_eeprom(129, 0x5A)
    def _load_init_para(self):
        """
        加载初始化参数文件

        :param self:
        :return:
        """
        # print(self.dev_id)
        # print(awg_para.keys())
        para_device = self.read_eeprom(0x80)
        para_status = self.read_eeprom(0x81)
        if para_device == 0xDA and para_status == 0x5A:
            self._calibrated_offset = [self.get_eeprom_para(i) for i in range(4)]
            self.diffampgain = [self.get_eeprom_para(i)/65536.0 for i in range(4,8)]
         #line = awg_para
         #line = line.strip('\n').split(':')
         #if line[0].strip() == self.dev_id or line[0].strip() == '000423':
         #   self._calibrated_offset = [int(i.strip()) for i in line[2].split(',')]
         #   self.diffampgain = [float(i.strip()) for i in line[1].split(',')]
         #   print(self._calibrated_offset, self.diffampgain)
         #   print('{0} initial paras loaded successfully'.format(self.dev_ip))
        else:
            print('warnning, {0} initial paras failed, defalt paras used'.format(self.dev_ip))
        
    def check_awg_status(self):
        # check if pll is locked
        # check if config is right
        # print(self.read_regs([[0x80, 0x38, 0]]))
        # print(self.read_regs([[0x81, 0x38, 0]]))
        sta1 = self.Read_Reg(1, 0x147)& 0xFF
        sta2 = self.Read_Reg(2, 0x147)& 0xFF
        assert sta1 == 0xc0 and sta2 == 0xc0, 'awg status check failed {0}, {1}'.format(hex(sta1), hex(sta2))
        # for addr in range(0x470,0x475):
        #     print(self.Read_Reg(1, addr))
        #     print(self.Read_Reg(1, addr))
    def InitBoard(self):
        """
        初始化AWG，该命令在AWG状态异常时使用,使AWG回到初始状态，并停止输出

        :param self:
        :return:
        """

        self.check_awg_status()
        self._load_init_para()
        self.Stop(1)
        self.Stop(2)
        self.Stop(3)
        self.Stop(4)
        for channel in range(self.channel_count):
            self._commit_para(channel + 1)
            self._SetDACMaxVolt(channel + 1, self.voltrange[channel] * self.diffampgain[channel])
            self.SetOffsetVolt(channel + 1, 0)

    def _upload_data(self, channel):
        """
        加载某一通道的波形数据与序列数据
        加载会导致相应的通道停止输出
        :param channel: AWG通道（1，2，3，4）
        :return:
        """
        self._channel_check(channel)
        self.Stop(channel)
        self._WriteWaveData(channel, self.waves[channel - 1])
        if self.has_ddr:
            self.load_data_to_ram(channel)
        self._WriteWaveCommands(channel, self.commands[channel - 1])
        # self.Start(1 << (channel - 1))
        # 还是由用户显示的启动AWG
    
    def lcm(self, a,b):
        gcd = lambda a, b: a if b == 0 else gcd(b, a % b)
        return a*b//gcd(a,b)

    def gen_iq_line(self, freq, phase=0, length=10e-6):
        """[生成正交调制的IQ信号]
        
        Arguments:
            freq {[integer]} -- [频率，单位Hz]
            phase {[float]} -- [相位，单位弧度]
            length {[float]} -- [单位，s]
        
        Returns:
            [numpy array] -- [iq 信号]
        """        
        # 多少个采样点：length*self.frequency
        # 多少个周期：length/(1/freq)*2*np.pi

        s_freq = self.lcm(freq, self.frequency)
        Oversampling = int(s_freq/self.frequency)
        size = int(length*s_freq)
        line = np.linspace(0,length/(1/freq)*2*np.pi, size)+phase
        line = line[::Oversampling]
        q_line = np.sin(line)
        i_line = np.cos(line)
        return [i_line, q_line]
    
    def generate_squr(self, period=10e-9, duty_ratio=0.5, rise_pos=0, low=-1.0, high=1.0):
        """
        单位为s

        :param period: 波形周期单位为秒
        :param duty_ratio: 波形占空比
        :param rise_pos: 高电平变化的时间
        :param low: 波形最小值，以电压表示
        :param high: 波形最大值，以电压表示
        :return:

        :notes::

            方波波形描述：频率，占空比，最大值，最小值，脉冲上升沿位置

        :assert::

            assert duty_ratio < 1
            assert rise_pos < period
            assert low >= -1
            assert high <= 1
            assert period <= 小于100us
        """
        assert duty_ratio < 1
        assert rise_pos < period
        assert low >= -1
        assert high <= 1
        assert period <= 100e-6
        total_cnt = int(period * self.frequency)
        high_pos = int(rise_pos * self.frequency)
        high_cnt = int(total_cnt * duty_ratio)
        unit = [low] * total_cnt
        # print(high_cnt, high_pos)
        unit[high_pos:high_pos + high_cnt] = [high] * high_cnt
        return unit
    
    def setSequenceStep(self,
                        index,
                        waveList,
                        wait=None,
                        goto='Next',
                        repeat=1,
                        delay=100e-6):
        """[设置 sequence 中第 index 步的波形、触发条件、跳转目标以及重复次数
            when index is 1, means start to generate sequence, the sequence parameter in awg will be clear
        ]

        Args:
            index ([int]): [step 标志，从1开始]
            waveList ([mix]): [list of wave array]
            wait ([str], optional): [wave outpt type]. Defaults to None.
            goto (str, optional): [next step of wave output]. Defaults to 'Next'.
            repeat (int, optional): [repetetion of wave output]. Defaults to 1.
            delay (int, optional): [when wait is delay, dekay mean the delay time between two output wave]. Defaults to 100us.
        """ 

        # 1. 将waveList中的波形分别写入对应分配的存储空间中，返回下一个可写入地址
        # 2. 用写入的起始地址和长度作为step参数
        assert 0 <= delay < 256e-6
        assert 0 < index 
        start_addrs = []
        next_addrs = []
        wave_sizes = []
        if index == 1:
            self.sequence = []
        # print(self.sequence)
        for idx,wave in enumerate(waveList):
            start_addr = 0 if index == 1 else self.sequence[index-2]['next_addrs'][idx]
            next_addr, wave_size = self.write_wave_to_ddr(idx+1, start_addr, wave, mark=None)
            start_addrs.append(start_addr)
            next_addrs.append(next_addr)
            wave_sizes.append(wave_size)
        _seq = {'start_addrs':start_addrs, 'next_addrs':next_addrs,'wave_sizes':wave_sizes, 'wait':wait, 'goto':goto, 'repeat':repeat, 'delay':delay}
        self.sequence.append(_seq)

    def playSequenceOn(self, *channels, wait_time=1e-3):
        """
        在目标通道上播放 sequence

        wait_time：两组波形间的切换等待时间，单位秒，默认1ms
        """
        self.gen_wave_control_from_sequence(wait_time)
        for idx,ch in enumerate(channels):
            self._WriteWaveCommands(ch, self.seq_dic[idx])
            # self.Start(ch)