import numpy as np
from scipy import interpolate
from scipy.signal import chirp,sweep_poly
# import matplotlib.pyplot as plt
from ._wavedata import Wavedata

### 重要的wd函数
def Sin(w, phi=0, width=0, sRate=1e2):
    timeFunc = lambda t: np.sin(w*t+phi)
    domain=(0,width)
    return Wavedata.init(timeFunc,domain,sRate)

def Cos(w, phi=0, width=0, sRate=1e2):
    timeFunc = lambda t: np.cos(w*t+phi)
    domain=(0,width)
    return Wavedata.init(timeFunc,domain,sRate)

def Exp(w, phi=0, width=0, sRate=1e2):
    '''IQ类型 复数正弦信号'''
    timeFunc = lambda t: np.exp(1j*(w*t+phi))
    domain=(0,width)
    return Wavedata.init(timeFunc,domain,sRate)


### 非IQ类型
def Blank(width=0, sRate=1e2):
    '''空波形'''
    timeFunc = lambda x: 0
    domain=(0, width)
    return Wavedata.init(timeFunc,domain,sRate)

def Noise_wgn(width=0, sRate=1e2):
    '''产生高斯白噪声序列，注意序列未归一化'''
    size = np.around(width * sRate).astype(int)
    data = np.random.randn(size)
    return Wavedata(data,sRate)

def DC(width=0, sRate=1e2):
    '''方波'''
    timeFunc = lambda x: 1
    domain=(0, width)
    return Wavedata.init(timeFunc,domain,sRate)

def Triangle(width=1, sRate=1e2):
    '''三角波'''
    timeFunc = lambda x: 1-np.abs(2/width*x)
    domain=(-0.5*width,0.5*width)
    return Wavedata.init(timeFunc,domain,sRate)

def Gaussian(width=1, sRate=1e2):
    '''高斯波形'''
    c = width/(4*np.sqrt(2*np.log(2)))
    timeFunc = lambda x: np.exp(-0.5*(x/c)**2)
    domain=(-0.5*width,0.5*width)
    return Wavedata.init(timeFunc,domain,sRate)

def Gaussian2(width=1,sRate=1e2,a=5):
    '''修正的高斯波形, a是width和方差的比值'''
    c = width/a # 方差
    # 减去由于截取造成的台阶, 使边缘为0, 并归一化
    y0 = np.exp(-0.5*(width/2/c)**2)
    timeFunc = lambda x: (np.exp(-0.5*(x/c)**2)-y0)/(1-y0)
    domain=(-0.5*width,0.5*width)
    return Wavedata.init(timeFunc,domain,sRate)

def CosPulse(width=1, sRate=1e2):
    timeFunc = lambda x: (np.cos(2*np.pi/width*x)+1)/2
    domain=(-0.5*width,0.5*width)
    return Wavedata.init(timeFunc,domain,sRate)

def Sinc(width=1, sRate=1e2, a=1):
    timeFunc = lambda t: np.sinc(a*t)
    domain=(-0.5*width,0.5*width)
    return Wavedata.init(timeFunc,domain,sRate)

def Interpolation(x, y, sRate=1e2, kind='linear'):
    '''参考scipy.interpolate.interp1d 插值'''
    timeFunc = interpolate.interp1d(x, y, kind=kind)
    domain = (x[0], x[-1])
    return Wavedata.init(timeFunc,domain,sRate)

def Chirp(f0, f1, width, sRate=1e2, phi=0, method='linear'):
    '''参考scipy.signal.chirp'''
    t1 = width # 结束点
    timeFunc = lambda t: chirp(t, f0, t1, f1, method=method, phi=phi, )
    domain = (0,t1)
    return Wavedata.init(timeFunc,domain,sRate)

def Sweep_poly(poly, width, sRate=1e2, phi=0):
    '''参考scipy.signal.sweep_poly 多项式频率'''
    timeFunc = lambda t: sweep_poly(t, poly, phi=0)
    domain = (0,width)
    return Wavedata.init(timeFunc,domain,sRate)


### IQ类型
def DRAGpulse(width=0, sRate=1e2, a=0.5, TYPE=CosPulse, **kw):
    '''IQ类型 DRAG波形,a为系数'''
    I = TYPE(width, sRate, **kw)
    amp=np.max(np.abs(I.data))
    Q=I.derivative()
    amp_drag=np.max(np.abs(Q.data))
    if amp_drag:
        Q.data *= (amp/amp_drag)
    Q *= a
    return I+1j*Q

def DRAG_wd(wd, a=0.5):
    '''IQ类型 DRAG给定的Wavedata类波形'''
    assert isinstance(wd, Wavedata)
    assert not wd.isIQ
    I = wd
    amp=np.max(np.abs(I.data))
    Q=I.derivative()
    # 将DRAG幅度用MHz表示，以便后续计算DRAG系数a，通常即为（拉比频率/非谐性）
    Q=1e-6*Q
    #amp_drag=np.max(np.abs(Q.data))
    #if amp_drag:
    #    Q.data *= (amp/amp_drag)
    Q *= a
    return I+1j*Q