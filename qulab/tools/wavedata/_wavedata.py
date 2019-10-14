import numpy as np
import matplotlib.pyplot as plt
from scipy import interpolate
from scipy.fftpack import fft,ifft


class Wavedata(object):

    def __init__(self, data = [], sRate = 1):
        '''给定序列和采样率，构造Wavedata'''
        self.data = np.array(data)
        self.sRate = sRate

    @staticmethod
    def generateData(timeFunc, domain=(0,1), sRate=1e2):
        '''给定函数、定义域、采样率，生成data序列'''
        length = np.around(abs(domain[1]-domain[0]) * sRate).astype(int) / sRate
        _domain = min(domain), (min(domain)+length)
        dt = 1/sRate
        _timeFunc = lambda x: timeFunc(x) * (x > _domain[0]) * ( x < _domain[1])
        x = np.arange(_domain[0]+dt/2, _domain[1], dt)
        data = np.array(_timeFunc(x))
        return data

    @classmethod
    def init(cls, timeFunc, domain=(0,1), sRate=1e2):
        '''给定函数、定义域、采样率，生成Wavedata类'''
        data = cls.generateData(timeFunc,domain,sRate)
        return cls(data,sRate)

    @property
    def isIQ(self):
        '''是否为IQ类型 即data是否包含复数'''
        return np.any(np.iscomplex(self.data))

    @property
    def x(self):
        '''返回波形的时间列表'''
        dt=1/self.sRate
        x = np.arange(dt/2, self.len, dt)
        return x

    @property
    def real(self):
        '''data实部'''
        return np.real(self.data)

    @property
    def imag(self):
        '''data虚部'''
        return np.imag(self.data)

    @property
    def f(self): # 支持复数与timeFunc一致
        '''返回根据属性data进行cubic类型插值得到的时间函数'''
        f = self.timeFunc(kind='cubic')
        return f

    @property
    def len(self):
        '''返回波形长度'''
        length = self.size/self.sRate
        return length

    @property
    def size(self):
        '''返回波形点数'''
        size = len(self.data)
        return size

    def I(self):
        '''I波形 返回Wavedata类'''
        w = self.__class__(np.real(self.data), self.sRate)
        return w

    def Q(self):
        '''Q波形 返回Wavedata类'''
        w = self.__class__(np.imag(self.data), self.sRate)
        return w

    def trans(self,mode='real'):
        '''对于IQ波形转化成其他几种格式'''
        if mode in ['amp','abs']: #振幅或绝对值
            data = np.abs(self.data)
        elif mode in ['phase','angle']: #相位或辐角
            data = np.angle(self.data,deg=True)
        elif mode == 'real': #实部
            data = np.real(self.data)
        elif mode == 'imag': #虚部
            data = np.imag(self.data)
        elif mode == 'conj': #复共轭
            data = np.conj(self.data)
        elif mode == 'exchange': #交换实部和虚部
            data = 1j*np.conj(self.data)
        w = self.__class__(data, self.sRate)
        return w

    def timeFunc(self,kind='cubic'):
        '''返回波形插值得到的时间函数，默认cubic插值'''
        #为了更好地插值，在插值序列x/y前后各加一个点，增大插值范围
        dt = 1/self.sRate
        x = np.arange(-dt/2, self.len+dt, dt)
        _y = np.append(0,self.data)
        y = np.append(_y,0)
        if self.isIQ:
            _timeFuncI = interpolate.interp1d(x,np.real(y),kind=kind,
                            bounds_error=False,fill_value=(0,0))
            _timeFuncQ = interpolate.interp1d(x,np.imag(y),kind=kind,
                            bounds_error=False,fill_value=(0,0))
            _timeFunc = lambda x: _timeFuncI(x) + 1j*_timeFuncQ(x)
        else:
            _timeFunc = interpolate.interp1d(x,y,kind=kind,
                            bounds_error=False,fill_value=(0,0))
        return _timeFunc

    def setLen(self,length):
        '''设置长度，增大补0，减小截取'''
        n = np.around(abs(length)*self.sRate).astype(int)
        return self.setSize(n)

    def setSize(self,size):
        '''设置点数，增多补0，减少截取'''
        n = np.around(size).astype(int)
        s = self.size
        if n > s:
            append_data=np.zeros(n-s)
            self.data = np.append(self.data, append_data)
        else:
            self.data = self.data[:n]
        return self

    def __call__(self, t):
        '''w(t) 返回某个时间点的最近邻值'''
        dt = 1/self.sRate
        idx = np.around(t/dt-0.5).astype(int)
        return self.data[idx]

    def __pos__(self):
        '''正 +w'''
        return self

    def __neg__(self):
        '''负 -w'''
        w = self.__class__(-self.data, self.sRate)
        return w

    def __abs__(self):
        '''绝对值 abs(w)'''
        w = self.__class__(np.abs(self.data), self.sRate)
        return w

    def __rshift__(self, t):
        '''右移 w>>t 长度不变'''
        if abs(t)>self.len:
            raise TypeError('shift is too large !')
        n = np.around(abs(t)*self.sRate).astype(int)
        shift_data = np.zeros(n)
        left_n = self.size-n
        if t>0:
            data = np.append(shift_data, self.data[:left_n])
        else:
            data = np.append(self.data[-left_n:], shift_data)
        w = self.__class__(data, self.sRate)
        return w

    def __lshift__(self, t):
        '''左移 t<<w 长度不变'''
        return self >> (-t)

    def __or__(self, other):
        '''或 w|o 串联波形'''
        assert isinstance(other,Wavedata)
        assert self.sRate == other.sRate
        data = np.append(self.data,other.data)
        w = self.__class__(data, self.sRate)
        return w

    def __xor__(self, n):
        '''异或 w^n 串联n个波形'''
        n = int(n)
        if n <= 1:
            return self
        else:
            data = list(self.data)*n
            w = self.__class__(data, self.sRate)
            return w

    def __pow__(self, v):
        '''幂 w**v 波形值的v次幂'''
        data = self.data ** v
        w = self.__class__(data, self.sRate)
        return w

    def __add__(self, other):
        '''加 w+o 波形值相加，会根据类型判断'''
        if isinstance(other,Wavedata):
            assert self.sRate == other.sRate
            size = max(self.size, other.size)
            self.setSize(size)
            other.setSize(size)
            data = self.data + other.data
            w = self.__class__(data, self.sRate)
            return w
        else:
            return other + self

    def __radd__(self, v):
        '''加 v+w 波形值加v，会根据类型判断'''
        data = self.data +v
        w = self.__class__(data, self.sRate)
        return w

    def __sub__(self, other):
        '''减 w-o 波形值相减，会根据类型判断'''
        return self + (- other)

    def __rsub__(self, v):
        '''减 v-w 波形值相减，会根据类型判断'''
        return v + (-self)

    def __mul__(self, other):
        '''乘 w*o 波形值相乘，会根据类型判断'''
        if isinstance(other,Wavedata):
            assert self.sRate == other.sRate
            size = max(self.size, other.size)
            self.setSize(size)
            other.setSize(size)
            data = self.data * other.data
            w = self.__class__(data, self.sRate)
            return w
        else:
            return other * self

    def __rmul__(self, v):
        '''乘 v*w 波形值相乘，会根据类型判断'''
        data = self.data * v
        w = self.__class__(data, self.sRate)
        return w

    def __truediv__(self, other):
        '''除 w/o 波形值相除，会根据类型判断'''
        if isinstance(other,Wavedata):
            assert self.sRate == other.sRate
            size = max(self.size, other.size)
            self.setSize(size)
            other.setSize(size)
            data = self.data / other.data
            w = self.__class__(data, self.sRate)
            return w
        else:
            return (1/other) * self

    def __rtruediv__(self, v):
        '''除 v/w 波形值相除，会根据类型判断'''
        data = v / self.data
        w = self.__class__(data, self.sRate)
        return w

    def convolve(self, other, mode='same', norm=True):
        '''卷积
        mode: full, same, valid'''
        if isinstance(other,Wavedata):
            _kernal = other.data
        elif isinstance(other,(np.ndarray,list)):
            _kernal = np.array(other)
        if norm:
            k_sum = sum(_kernal)
            kernal = _kernal / k_sum   #归一化kernal，使卷积后的波形总幅度不变
        else:
            kernal = _kernal
        data = np.convolve(self.data,kernal,mode)
        w = self.__class__(data, self.sRate)
        return w

    def FFT(self, mode='complex', half=True, **kw): # 支持复数，需做调整
        '''FFT, 默认波形data为实数序列, 只取一半结果, 为实际物理频谱'''
        sRate = self.size/self.sRate
        # 对于实数序列的FFT，正负频率的分量是相同的
        # 对于双边谱，即包含负频率成分的，除以size N 得到实际振幅
        # 对于单边谱，即不包含负频成分，实际振幅是正负频振幅的和，
        # 所以除了0频成分其他需要再乘以2
        fft_data = fft(self.data)/self.size
        if mode in ['amp','abs']:
            data = np.abs(fft_data)
        elif mode in ['phase','angle']:
            data = np.angle(fft_data,deg=True)
        elif mode == 'real':
            data = np.real(fft_data)
        elif mode == 'imag':
            data = np.imag(fft_data)
        elif mode == 'complex':
            data = fft_data
        if half:
            #size N为偶数时，取N/2；为奇数时，取(N+1)/2
            index = int((len(data)+1)/2)
            data = data[:index]
            data[1:] = data[1:]*2 #非0频成分乘2
        w = self.__class__(data, sRate)
        return w

    def getFFT(self,freq,mode='complex',half=True,**kw):
        ''' 获取指定频率的FFT分量；
        freq: 为一个频率值或者频率的列表，
        返回值: 是对应mode的一个值或列表'''
        freq_array=np.array(freq)
        fft_w = self.FFT(mode=mode,half=half,**kw)
        index_freq = np.around(freq_array*fft_w.sRate).astype(int)
        res_array = fft_w.data[index_freq]
        return res_array
    
    def transfer_wd(self,transfer_func,**kw):
        # transfer_func example
        # transfer_func = lambda w: 1+1j*0.01*w/(1j*w+1e9/10)
        #                            +1j*0.005*w/(1j*w+1e9/20)
        #                            +1j*0.003*w/(1j*w+1e9/30)
        fft_data = fft(self.data)
        
        # size N为偶数时，取N/2；为奇数时，取(N+1)/2
        index = int((len(fft_data)+1)/2)
        # 获取和fft_data对应的真实频谱频率
        x_1 = np.array([n for n in range(index)])
        if len(fft_data)%2==0:
            x_2 = np.array([n for n in range(index)])+1
            x_2 = -x_2[::-1]
        else:
            x_2 = np.array([n for n in range(index-1)])+1
            x_2 = -x_2[::-1]
        freq = 2*np.pi*np.append(x_1,x_2)*self.sRate/self.size
        # 根据transfer_func修正波形的频谱，然后再从新生成波形
        transfer_factor = np.array(transfer_func(freq))
        fft_data = np.array(fft_data)*transfer_factor
        self.data = ifft(fft_data,**kw)
        return self
    

    def high_resample(self,sRate,kind='nearest'): # 复数支持与timeFunc一致
        '''提高采样率重新采样'''
        assert sRate > self.sRate
        timeFunc = self.timeFunc(kind=kind)
        domain = (0,self.len)
        w = self.init(timeFunc,domain,sRate)
        return w

    def low_resample(self,sRate,kind='linear'): # 复数支持与timeFunc一致
        '''降低采样率重新采样'''
        assert sRate < self.sRate
        timeFunc = self.timeFunc(kind=kind)
        domain = (0,self.len)
        w = self.init(timeFunc,domain,sRate)
        return w

    def resample(self,sRate): # 复数支持与timeFunc一致
        '''改变采样率重新采样'''
        if sRate == self.sRate:
            return self
        elif sRate > self.sRate:
            return self.high_resample(sRate)
        elif sRate < self.sRate:
            return self.low_resample(sRate)

    def normalize(self):
        '''归一化 取实部和虚部绝对值的最大值进行归一，使分布在(-1,+1)'''
        v_max = max(abs(np.append(np.real(self.data),np.imag(self.data))))
        self.data = self.data/v_max
        return self

    def derivative(self):
        '''求导，点数不变'''
        y1=np.append(0,self.data[:-1])
        y2=np.append(self.data[1:],0)
        diff_data = (y2-y1)/2 #差分数据，间隔1个点做差分
        data = diff_data*self.sRate #导数，差分值除以 dt
        w = self.__class__(data,self.sRate)
        return w

    def integrate(self):
        '''求积分，点数不变'''
        cumsum_data = np.cumsum(self.data) #累积
        data = cumsum_data/self.sRate #积分，累积值乘以 dt
        w = self.__class__(data,self.sRate)
        return w

    def process(self,func,**kw): # 根据具体情况确定是否支持复数
        '''处理，传入一个处理函数func, 输入输出都是(data,sRate)格式'''
        data,sRate = func(self.data,self.sRate,**kw) # 接受额外的参数传递给func
        return self.__class__(data,sRate)

    def filter(self,filter): # 根据具体情况确定是否支持复数
        '''调用filter的process函数处理；
        一般filter是本模块里的Filter类'''
        assert hasattr(filter,'process')
        w = self.process(filter.process)
        return w

    def plot(self, fmt1='', fmt2='--', isfft=False, **kw):
        '''对于FFT变换后的波形数据，包含0频成分，x从0开始；
        使用isfft=True会去除了x的偏移，画出的频谱更准确'''
        ax = plt.gca()
        if isfft:
            dt=1/self.sRate
            x = np.arange(0, self.len-dt/2, dt)
        else:
            x = self.x
        if self.isIQ:
            ax.set_title('Wavedata-IQ')
            ax.plot(x, np.real(self.data), fmt1, label='real', **kw)
            ax.plot(x, np.imag(self.data), fmt2, label='imag', **kw)
            plt.legend(loc = 'best')
        else:
            ax.set_title('Wavedata')
            ax.plot(x, self.data, fmt1, **kw)

    def plt(self, mode='psd', r=False, **kw): # 支持复数，需要具体了解
        '''调用pyplot里与频谱相关的函数画图
        mode 可以为 psd,specgram,magnitude_spectrum,angle_spectrum,
        phase_spectrum等5个(cohere,csd需要两列数据，这里不支持)'''
        ax = plt.gca()
        plt_func = getattr(plt,mode)
        res = plt_func(x=self.data,Fs=self.sRate,**kw)
        if r:
            return res
