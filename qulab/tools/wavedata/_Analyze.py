import numpy as np
import copy
import matplotlib.pyplot as plt
from ._wavedata import Wavedata
from ._wd_func import *


'''Wavedata 额外的分析模块，传入Wavedata类实例，进行分析'''


def Homodyne(wd, freq=50e6, cali=None, DEG=True):
    '''把信号按一定频率旋转，得到解调的IQ'''
    if cali is None:
        res_wd=wd*Exp(-2*np.pi*freq,0,wd.len,wd.sRate)
        return res_wd
    else:
        _cali = np.array(cali)
        _scale_I, _offset_I = _cali[0,:2]
        _scale_Q, _offset_Q = _cali[1,:2]
        #转为弧度
        _phi_I, _phi_Q = _cali[:,2]*np.pi/180 if DEG else _cali[:,2]

        # 相位校准，等效于进行波形时移，时移大小由相位误差、频率等决定
        shift_I = _phi_I/(2*np.pi*freq) if not freq==0 else 0
        shift_Q = _phi_Q/(2*np.pi*freq) if not freq==0 else 0

        # 相位校准，将I/Q插值函数平移后重新采样
        func_I = lambda x: wd.I().timeFunc(kind='cubic')(x-shift_I)
        _wd_I = Wavedata.init(func_I,(0,wd.len),wd.sRate)
        func_Q = lambda x: wd.Q().timeFunc(kind='cubic')(x-shift_Q)
        _wd_Q = Wavedata.init(func_Q,(0,wd.len),wd.sRate)

        # 反向校准，与vIQmixer中carry_wave校准相反
        _wd_I=(_wd_I-_offset_I)/_scale_I
        _wd_Q=(_wd_Q-_offset_Q)/_scale_Q

        _wd=_wd_I+1j*_wd_Q
        res_wd=_wd*Exp(-2*np.pi*freq,0,wd.len,wd.sRate)
        return res_wd

def Analyze_cali(wd, freq=50e6, DEG=True):
    '''根据IQ波形计算校正序列,准确性好'''
    para_I=wd.I().getFFT([0,freq],mode='complex',half=True)
    para_Q=wd.Q().getFFT([0,freq],mode='complex',half=True)

    _offset_I,_offset_Q = para_I[0].real,para_Q[0].real
    amp_I,amp_Q = np.abs(para_I[1]),np.abs(para_Q[1])
    phase_I,phase_Q = np.angle(para_I[1],deg=DEG),np.angle(para_Q[1],deg=DEG)

    _scale_I, _scale_Q = 1, amp_Q/amp_I
    phi0 = 90 if DEG else np.pi/2
    _phase_I, _phase_Q = 0, phase_Q-phase_I+phi0

    cali_array = np.array([[_scale_I,_offset_I,_phase_I],
                           [_scale_Q,_offset_Q,_phase_Q]]
                          ).round(decimals=3) # 保留3位小数
    return cali_array
