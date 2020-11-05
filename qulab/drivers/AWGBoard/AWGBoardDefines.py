# 	FileName:AWGboard_defines.py
# 	Modified: 2018.2.18
#   Description:The command and status define class of AWG


class AWGBoardDefines:
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

    AWG_CMD_CONTINUE    = 0x0 << 11
    AWG_CMD_COUNT       = 0x4 << 11
    AWG_CMD_TRIG        = 0x8 << 11
    AWG_CMD_NULL_CNT    = 0x5 << 11
    AWG_CMD_NULL_TRIG   = 0x3 << 11
    AWG_CMD_WAIT_DDR    = 0x9 << 11
    AWG_CMD_READ2RAM    = 0xA << 11
    AWG_CMD_READ2FIFO   = 0xB << 11
    AWG_CMD_NULL_LOOP_S = 0x6 << 11
    AWG_CMD_NULL_LOOP_E = 0x7 << 11
    

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
