# 	FileName:AWGboard_defines.py
# 	Modified: 2018.2.18
#   Description:The command and status define class of AWG


class BoardDefines:
    """
   AWG常量定义
   """

    def __init__(self):
        pass
    CMD_NON_VAL = 0x0
    CMD_READ_REG = 0x55555555
    CMD_WRITE_REG = 0xAAAAAAAA
    CMD_READ_MEM = 0xAA5555AA
    CMD_WRITE_MEM = 0x55AAAA55
    CMD_LAST = CMD_WRITE_MEM
    CHIP_NON_VAL = 0x0
    CHIP_9136_1 = 0x1
    CHIP_9136_2 = 0x2
    CHIP_2582 = 0x3
    CHIP_AWG_1 = 0x4
    CHIP_AWG_2 = 0x5
    CHIP_LAST = CHIP_AWG_2

    REGREG_NON_VAL = 0x00
    REG_IDNTITY = 0x00
    REG_VERSION = 0x04
    REG_SY_STAT = 0x08
    REG_TESTREG = 0x0C
    REG_CNFG_REG0 = 0x80
    REG_CNFG_REG1 = 0x84
    REG_CNFG_REG2 = 0x88
    REG_CNFG_REG3 = 0x8C
    REG_CNFG_REG4 = 0xC0
    REG_CNFG_REG5 = 0x114
    REG_CTRL_REG = 0xD0
    REG_STATUS_1 = 0x100
    REG_STATUS_2 = 0x104
    REG_LAST = REG_STATUS_2
    CTRL_CH1_RUN = 0
    CTRL_CH2_RUN = 1
    CTRL_CH1_STOP = 4
    CTRL_CH2_STOP = 5

    CNFG4_CH1_CMD_CS = 0
    CNFG4_CH2_CMD_CS = 1
    CNFG4_CH1_WAV_CS = 4
    CNFG4_CH2_WAV_CS = 5
    CNFG4_CH1_RD_BACK = 8
    CNFG4_CH2_RD_BACK = 9

    STAT_SUCCESS = 0x0
    STAT_ERROR = 0x1
    STAT_CMDERR = 0x2
    STAT_RDERR = 0x3
    STAT_WRERR = 0x4
    STAT_MEM_RANGE_ERR = 0x5
    STAT_MEM_ALIGN_ERR = 0x6
    STAT_SIZE_ERR = 0x7
    STAT_SIZE_ALIGN_ERR = 0x8
    STAT_ADDR_ALIGN_ERR = 0x9
    STAT_LAST = STAT_ADDR_ALIGN_ERR
    
    REF_10MHz_CONFIG = ['./fpga_tool spi1_wr 0x00 0x2216',
                        './fpga_tool spi1_wr 0x00 0x2214',
                        './fpga_tool spi1_wr 0x40 0x0077',
                        './fpga_tool spi1_wr 0x3e 0x0000',
                        './fpga_tool spi1_wr 0x3d 0x0000',
                        './fpga_tool spi1_wr 0x3b 0x0000',
                        './fpga_tool spi1_wr 0x30 0x03fc',
                        './fpga_tool spi1_wr 0x2f 0x00de',
                        './fpga_tool spi1_wr 0x2e 0x1f21',
                        './fpga_tool spi1_wr 0x2d 0x0000',
                        './fpga_tool spi1_wr 0x2c 0x0000',
                        './fpga_tool spi1_wr 0x2b 0x0000',
                        './fpga_tool spi1_wr 0x2a 0x0000',
                        './fpga_tool spi1_wr 0x29 0x001f',
                        './fpga_tool spi1_wr 0x28 0x0000',
                        './fpga_tool spi1_wr 0x27 0x8104',
                        './fpga_tool spi1_wr 0x26 0x00c8',
                        './fpga_tool spi1_wr 0x25 0x4000',
                        './fpga_tool spi1_wr 0x24 0x0c21',
                        './fpga_tool spi1_wr 0x23 0x109b',
                        './fpga_tool spi1_wr 0x22 0xc3EA',
                        './fpga_tool spi1_wr 0x21 0x2A0A',
                        './fpga_tool spi1_wr 0x20 0x210A',
                        './fpga_tool spi1_wr 0x1f 0x0601',
                        './fpga_tool spi1_wr 0x1e 0x0034',
                        './fpga_tool spi1_wr 0x1d 0x0084',
                        './fpga_tool spi1_wr 0x1c 0x2924',
                        './fpga_tool spi1_wr 0x19 0x0000',
                        './fpga_tool spi1_wr 0x18 0x0509',
                        './fpga_tool spi1_wr 0x17 0x8842',
                        './fpga_tool spi1_wr 0x16 0x2300',
                        './fpga_tool spi1_wr 0x14 0x012c',
                        './fpga_tool spi1_wr 0x13 0x0965',
                        './fpga_tool spi1_wr 0x0e 0x0FFD',
                        './fpga_tool spi1_wr 0x0d 0x4000',
                        './fpga_tool spi1_wr 0x0c 0x7001',
                        './fpga_tool spi1_wr 0x0b 0x0018',
                        './fpga_tool spi1_wr 0x0a 0x10d8',
                        './fpga_tool spi1_wr 0x09 0x0b02',
                        './fpga_tool spi1_wr 0x08 0x1084',
                        './fpga_tool spi1_wr 0x07 0x28b2',
                        './fpga_tool spi1_wr 0x04 0x1943',
                        './fpga_tool spi1_wr 0x02 0x0500',
                        './fpga_tool spi1_wr 0x01 0x0808',
                        './fpga_tool spi1_wr 0x00 0x221c',]
    
    REF_250MHz_CONFIG = ['./fpga_tool spi1_wr 0x00 0x2216',
                         './fpga_tool spi1_wr 0x00 0x2214',
                         './fpga_tool spi1_wr 0x40 0x0077',
                         './fpga_tool spi1_wr 0x3e 0x0000',
                         './fpga_tool spi1_wr 0x3d 0x0000',
                         './fpga_tool spi1_wr 0x3b 0x0000',
                         './fpga_tool spi1_wr 0x30 0x03fc',
                         './fpga_tool spi1_wr 0x2f 0x00df',
                         './fpga_tool spi1_wr 0x2e 0x1f20',
                         './fpga_tool spi1_wr 0x2d 0x0000',
                         './fpga_tool spi1_wr 0x2c 0x0000',
                         './fpga_tool spi1_wr 0x2b 0x0000',
                         './fpga_tool spi1_wr 0x2a 0x0000',
                         './fpga_tool spi1_wr 0x29 0x0001',
                         './fpga_tool spi1_wr 0x28 0x0000',
                         './fpga_tool spi1_wr 0x27 0x8104',
                         './fpga_tool spi1_wr 0x26 0x0014',
                         './fpga_tool spi1_wr 0x25 0x4000',
                         './fpga_tool spi1_wr 0x24 0x0c21',
                         './fpga_tool spi1_wr 0x23 0x109b',
                         './fpga_tool spi1_wr 0x22 0xc3EA',
                         './fpga_tool spi1_wr 0x21 0x2A0A',
                         './fpga_tool spi1_wr 0x20 0x210A',
                         './fpga_tool spi1_wr 0x1f 0x0601',
                         './fpga_tool spi1_wr 0x1e 0x0034',
                         './fpga_tool spi1_wr 0x1d 0x0084',
                         './fpga_tool spi1_wr 0x1c 0x2924',
                         './fpga_tool spi1_wr 0x19 0x0000',
                         './fpga_tool spi1_wr 0x18 0x0509',
                         './fpga_tool spi1_wr 0x17 0x8842',
                         './fpga_tool spi1_wr 0x16 0x2300',
                         './fpga_tool spi1_wr 0x14 0x012c',
                         './fpga_tool spi1_wr 0x13 0x0965',
                         './fpga_tool spi1_wr 0x0e 0x0fff',
                         './fpga_tool spi1_wr 0x0d 0x4000',
                         './fpga_tool spi1_wr 0x0c 0x700a',
                         './fpga_tool spi1_wr 0x0b 0x0018',
                         './fpga_tool spi1_wr 0x0a 0x1258',
                         './fpga_tool spi1_wr 0x09 0x0b02',
                         './fpga_tool spi1_wr 0x08 0x1084',
                         './fpga_tool spi1_wr 0x07 0x28b2',
                         './fpga_tool spi1_wr 0x04 0x1943',
                         './fpga_tool spi1_wr 0x02 0x0500',
                         './fpga_tool spi1_wr 0x01 0x0808',
                         './fpga_tool spi1_wr 0x00 0x239c',]