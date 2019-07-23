import numpy as np
import matplotlib.pyplot as plt
from scipy.fftpack import fft,ifft

'''Wavedata 额外的处理模块，包含一些自定义的处理功能'''

def normalize(data, sRate):
    '''归一化波形，使其分布在(-1,+1)'''
    v_max = max(abs(np.append(np.real(data),np.imag(data))))
    _data = data/v_max
    return _data, sRate

def integrate(data, sRate):
    '''求积分，点数不变'''
    cumsum_data = np.cumsum(data) #累积
    _data = cumsum_data/sRate #积分，累积值乘以 dt
    return _data, sRate

def derivative(data, sRate):
    '''求导，点数不变'''
    y1=np.append(0,data[:-1])
    y2=np.append(data[1:],0)
    diff_data = (y2-y1)/2 #差分数据，间隔1个点做差分
    _data = diff_data*sRate #导数，差分值除以 dt
    return _data, sRate

def FFT(data, sRate, mode='amp',half=True,**kw):
    '''FFT, 默认波形data为实数序列, 只取一半结果, 为实际物理频谱'''
    size = len(data)
    _sRate = size/sRate
    # 对于实数序列的FFT，正负频率的分量是相同的
    # 对于双边谱，即包含负频率成分的，除以size N 得到实际振幅
    # 对于单边谱，即不包含负频成分，实际振幅是正负频振幅的和，所以除了0频成分其他需要再乘以2
    fft_data = fft(data,**kw)/size
    if mode in ['amp','abs']:
        _data =np.abs(fft_data)
    elif mode in ['phase','angle']:
        _data =np.angle(fft_data,deg=True)
    elif mode == 'real':
        _data =np.real(fft_data)
    elif mode == 'imag':
        _data =np.imag(fft_data)
    elif mode == 'complex':
        _data = fft_data
    if half:
        #size N为偶数时，取N/2；为奇数时，取(N+1)/2
        index = int((len(_data)+1)/2)-1
        _data = _data[:index]
        _data[1:] = _data[1:]*2 #非0频成分乘2
    return _data, _sRate
