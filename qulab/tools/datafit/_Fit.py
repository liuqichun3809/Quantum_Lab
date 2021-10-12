import numpy as np
from scipy import stats
import matplotlib.ticker as ticker
from scipy.constants import hbar
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit



class BaseFit(object):
    """BaseFit class, based on scipy.optimiz.curve_fit """
    def __init__(self, data, **kw):
        super(BaseFit, self).__init__()
        self.data=np.array(data)
        self._Fitcurve(**kw)

    def _fitfunc(self, t, A, B, T1):
        '''this an example: T1 fit function '''
        y=A*np.exp(-t/T1)+B
        return y

    def _Fitcurve(self, **kw):
        t,y=self.data
        popt, pcov=curve_fit(self._fitfunc, t, y, maxfev=100000, **kw)
        self._popt = popt
        self._pcov = pcov
        self._error = np.sqrt(np.diag(pcov))

    def plot(self, fmt2='k--',
                   kw1={},
                   kw2={}):
        ax = plt.gca()
        t,y=self.data
        scatter_kw={'marker':'o','color':'','edgecolors':'r'}
        scatter_kw.update(kw1)
        ax.scatter(t, y, **scatter_kw)
        plot_kw={}
        plot_kw.update(kw2)
        ax.plot(t, self._fitfunc(t,*self._popt), fmt2, **plot_kw)

    @property
    def error(self):
        '''standard deviation errors on the parameters '''
        return self._error

    @property
    def params(self):
        '''optimized parameters '''
        return self._popt


class Cauchy_Fit(BaseFit):
    '''Fit peak'''

    def _fitfunc(self,t,A,t0,FWHM):
        y=A*FWHM/((t-t0)**2+FWHM**2)/np.pi
        return y

    @property
    def t0(self):
        A,t0,FWHM=self._popt
        return t0

    @property
    def t0_error(self):
        A_e,t0_e,FWHM_e=self._error
        return t0_e

    @property
    def FWHM(self):
        A,t0,FWHM=self._popt
        return FWHM

    @property
    def FWHM_error(self):
        A_e,t0_e,FWHM_e=self._error
        return FWHM_e


class Linear_Fit(BaseFit):
    '''Simple Linear Fit'''

    def _fitfunc(self,t,A,B):
        y= A * t + B
        return y

    @property
    def A(self):
        A,B=self._popt
        return A

    @property
    def B(self):
        A,B=self._popt
        return B


class Sin_Fit(BaseFit):
    def _fitfunc(self, t, A, B, w, phi):
        y=A*np.sin(w*t+phi)+B
        return y


class LRZ_Fit(BaseFit):
    """Lorenz Fit, fit_tag can be 'real', 'imag' or 'amp' """
    def __init__(self, data, fit_tag='real', **kw):
        super(BaseFit, self).__init__()
        self.data=np.array(data)
        self.fit_tag = fit_tag
        self._Fitcurve(**kw)

    def _fitfunc(self, t, f_center, kappa_int, kappa_ext):
        # when fitting the amp, kappa_ext is the amp, kappa_int is the real kappa
        if self.fit_tag == 'real':
            y=1-2*kappa_ext/((kappa_int+kappa_ext)*(1+(2*(t-f_center)/(kappa_int+kappa_ext))**2))
        elif self.fit_tag == 'imag':
            y=2*kappa_ext*(2*(t-f_center)/(kappa_int+kappa_ext))/((kappa_int+kappa_ext)*(1+(2*(t-f_center)/(kappa_int+kappa_ext))**2))
        else:
            y=kappa_ext*kappa_int**2/(4*(t-f_center)**2+kappa_int**2)
        return y

    def _Fitcurve(self, **kw):
        t,y=self.data
        popt, pcov=curve_fit(self._fitfunc, t, y, maxfev=100000, **kw)
        self._popt = popt
        self._pcov = pcov
        self._error = np.sqrt(np.diag(pcov))

    def plot(self, fmt2='k--',
                   kw1={},
                   kw2={}):
        ax = plt.gca()
        t,y=self.data
        scatter_kw={'marker':'o','color':'','edgecolors':'r'}
        scatter_kw.update(kw1)
        ax.scatter(t, y, **scatter_kw)
        plot_kw={}
        plot_kw.update(kw2)
        ax.plot(t, self._fitfunc(t,*self._popt), fmt2, **plot_kw)

    @property
    def error(self):
        '''standard deviation errors on the parameters '''
        return self._error

    @property
    def params(self):
        '''optimized parameters '''
        return self._popt
    
    @property
    def f_center(self):
        f_center, kappa_int, kappa_ext = self._popt
        return f_center
    
    @property
    def kappa_int(self):
        f_center, kappa_int, kappa_ext = self._popt
        return kappa_int
    
    @property
    def kappa_ext(self):
        f_center, kappa_int, kappa_ext = self._popt
        return kappa_ext

# S参数曲线拟合
class S_Fit(BaseFit):
    def __init__(self, data, fit_tag='S11',**kw):
        super(BaseFit, self).__init__()
        self.data=np.array(data)
        self.fit_tag=fit_tag
        
        ## 初步处理
        # 幅度归一
        self.A = max(abs(self.data[1]))
        self.data[1] = self.data[1]/self.A
        # 去除线路延时
        self.get_delay()
        self.cancel_delay()
        
        ## 主体拟合，获取幅度A、阻抗失配phi、线宽kappa_ext和kappa_int、谐振频率f_c
        # 获取初始拟合值
        self.data[0] = abs(self.data[0])
        if 'p0' in kw:
            p0 = kw['p0']
        else:
            A = 1
            alpha = 0
            delay = 0
            phi = 0
            kappa = abs(self.data[0][-1]-self.data[0][0])/10
            f_c = abs(self.data[0][0]+self.data[0][-1])/2
            Q_l = f_c/kappa
            if 'weak' in self.fit_tag:
                Q_c = 4*Q_l
            else:
                Q_c = 1.5*Q_l
            p0 = [A,alpha,delay,phi,Q_l,Q_c,f_c]
        self._Fitcurve(p0=p0)
        
        ## 相位拟合，获取准确初始相位alpha，延迟delay
        # 获取初始拟合值
        if 'p0' in kw:
            p0 = kw['p0']
        else:
            A = self._popt[0]
            alpha = np.unwrap(np.angle(self.data[1]))[0]
            delay = 0
            phi = self._popt[3]
            Q_l = self._popt[4]
            Q_c = self._popt[5]
            f_c = self._popt[6]
            p0 = [A,alpha,delay,phi,Q_l,Q_c,f_c]
        self._Fitcurve_phase(p0=p0)
        
        ## 将线性标准化
        self.normalization()
    
    
    ## 主体拟合
    def _fitfunc(self,t,A,alpha,delay,phi,Q_l,Q_c,f_c):
        delay = 0
        alpha = 0
        if 'S11' in self.fit_tag:
            S = A*np.exp(1j*alpha)*np.exp(-2*np.pi*1j*t*delay)*(1-(abs(Q_l)/abs(Q_c)*np.exp(1j*phi))/(1+2j*abs(Q_l)*(t/f_c-1)))
        else:
            S = A*np.exp(1j*alpha)*np.exp(-2*np.pi*1j*t*delay)*(abs(Q_l)/abs(Q_c)*np.exp(1j*phi))/(1+2j*abs(Q_l)*(t/f_c-1))
        return abs(S)
    
    def _Fitcurve(self, **kw):
        t,y=self.data
        y = abs(y)
        popt, pcov=curve_fit(self._fitfunc, t, y, maxfev=100000, **kw)
        self._popt = popt
        self._pcov = pcov
        self._error = np.sqrt(np.diag(pcov))
    
    ## 相位拟合，获取准确初始相位alpha，延迟delay
    def _fitfunc_phase(self,t,A,alpha,delay,phi,Q_l,Q_c,f_c):
        A = 1
        if 'S11' in self.fit_tag:
            S = A*np.exp(1j*alpha)*np.exp(-2*np.pi*1j*t*delay)*(1-(abs(Q_l)/abs(Q_c)*np.exp(1j*phi))/(1+2j*abs(Q_l)*(t/f_c-1)))
        else:
            S = A*np.exp(1j*alpha)*np.exp(-2*np.pi*1j*t*delay)*(abs(Q_l)/abs(Q_c)*np.exp(1j*phi))/(1+2j*abs(Q_l)*(t/f_c-1))
        return np.unwrap(np.angle(S))
    
    def _Fitcurve_phase(self, **kw):
        t,y=self.data
        y = np.unwrap(np.angle(y))
        popt, pcov=curve_fit(self._fitfunc_phase, t, y, maxfev=100000, **kw)
        self._popt_phase = popt
        self._pcov_phase = pcov
        self._error_phase = np.sqrt(np.diag(pcov))
    
    ## 获取初始延时
    def get_delay(self):
        f_para = self.data[0]
        S_para = self.data[1]
        length = len(f_para)
        if 'weak' in self.fit_tag:
            f_para = np.hstack([f_para[:int(length/5)],f_para[-int(length/5):]])
            phase = np.unwrap(np.angle(S_para))
            phase = np.hstack([phase[:int(length/5)],phase[-int(length/5):]])
            gradient, intercept, r_value, p_value, std_err = stats.linregress(abs(f_para),phase)
            self.delay = gradient/(np.pi*2.)
        else:
            phase = np.unwrap(np.angle(S_para))
            gradient, intercept, r_value, p_value, std_err = stats.linregress(abs(f_para),phase)
            self.delay = (gradient-(-np.pi*2./abs(f_para[-1]-f_para[0])))/(np.pi*2.)
        return self.delay
    
    ## 去除延时
    def cancel_delay(self):
        self.data[1] = self.data[1]*np.exp(2*1j*np.pi*(-self.delay)*self.data[0])
        phase = np.unwrap(np.angle(self.data[1]))
        self.data[1] = (np.cos(phase[0])-1j*np.sin(phase[0]))*self.data[1]
        
        phase = np.unwrap(np.angle(self.data[1]))
        if abs(np.pi-phase[0])<np.pi/10:
            self.data[1] = -self.data[1]
        return self.data
    
    ## 将线形标准化
    def normalization(self):
        self.data[1] = self.data[1]/self._popt[0]*np.exp(-1j*self._popt_phase[1])*np.exp(2*np.pi*1j*self.data[0]*self._popt_phase[2])
        return self.data
    
    def S_fit_result(self,t,A,alpha,delay,phi,Q_l,Q_c,f_c):
        if 'S11' in self.fit_tag:
            S = A*np.exp(1j*alpha)*np.exp(-2*np.pi*1j*t*delay)*(1-(abs(Q_l)/abs(Q_c)*np.exp(1j*phi))/(1+2j*abs(Q_l)*(t/f_c-1)))
        else:
            S = A*np.exp(1j*alpha)*np.exp(-2*np.pi*1j*t*delay)*(abs(Q_l)/abs(Q_c)*np.exp(1j*phi))/(1+2j*abs(Q_l)*(t/f_c-1))
        return S
    
    def get_single_photon_limit(self,unit='dBm'):
        fr = self.params[6]
        k_c = 2*np.pi*self.params[4]
        k_i = 2*np.pi*self.params[5]
        if unit=='dBm':
            return 10.*np.log10(1000./(4.*k_c/(2.*np.pi*hbar*fr*(k_c+k_i)**2)))
        else:
            return 1./(4.*k_c/(2.*np.pi*hbar*fr*(k_c+k_i)**2))
        
    def get_photons_in_resonator(self,power,unit='dBm',diacorr=True):
        if unit=='dBm':
            power = 10**(power/10.) /1000.
        fr = self.params[6]
        k_c = 2*np.pi*self.params[4]
        k_i = 2*np.pi*self.params[5]
        return 4.*k_c/(2.*np.pi*hbar*fr*(k_c+k_i)**2) * power 
    
    def plot(self,fig):
        t,y=self.data
        S_result = self.S_fit_result(t,1,0,0,self._popt[3],self._popt[4],self._popt[5],self._popt[6])
        # 绘图
        ax1 = fig.add_subplot(221)
        ax1.plot(np.real(y),np.imag(y),'ro')
        ax1.plot(np.real(S_result),np.imag(S_result),'b-')
        ax1.set_xlabel('Re(S21)')
        ax1.set_ylabel('Im(S21)')
        ax2 = fig.add_subplot(222)
        ax2.plot(t/1e9,abs(y),'ro')
        ax2.plot(t/1e9,abs(S_result),'b-')
        ax2.xaxis.set_major_formatter(ticker.FormatStrFormatter('%.3f'))
        ax2.set_xlabel('freq(GHz)')
        ax2.set_ylabel('|S21|')
        ax3 = fig.add_subplot(223)
        ax3.plot(t/1e9,np.unwrap(np.angle(y)),'ro')
        ax3.plot(t/1e9,np.unwrap(np.angle(S_result)),'b-')
        ax3.xaxis.set_major_formatter(ticker.FormatStrFormatter('%.3f'))
        ax3.set_xlabel('freq(GHz)')
        ax3.set_ylabel('phase')
        ax4 = fig.add_subplot(224)
        ax4.plot([-0.5,1.5],[-0.5,1.5],'.')
        ax4.set_xlim(0,1)
        ax4.set_ylim(0,1)
        ax4.set_xticks(ticks=[])
        ax4.set_yticks(ticks=[])
        ax4.text(0.5,0.9,'f = '+str(round(self.params[6]/1e9,6))+'GHz',verticalalignment='center',horizontalalignment='center')
        ax4.text(0.5,0.75,'Q_int = '+str(round(self.params[6]/self.params[5]/1e3,1))+'k',verticalalignment='center',horizontalalignment='center')
        ax4.text(0.5,0.6,'kappa_int = '+str(round(self.params[5]/1e3,1))+'kHz',verticalalignment='center',horizontalalignment='center')
        ax4.text(0.5,0.45,'kappa_ext = '+str(round(self.params[4]/1e3,1))+'kHz',verticalalignment='center',horizontalalignment='center')
        ax4.text(0.5,0.3,'delay = '+str(round(self.params[2]*1e9,1))+'ns',verticalalignment='center',horizontalalignment='center')
        ax4.text(0.5,0.15,'mis-match = '+str(round(self.params[3],3)),verticalalignment='center',horizontalalignment='center')
        
        """
        plt.subplot(221)
        plt.plot(np.real(y),np.imag(y),'ro')
        plt.plot(np.real(S_result),np.imag(S_result),'b-')
        plt.xlabel('Re(S21)')
        plt.ylabel('Im(S21)')
        plt.legend()
        plt.subplot(222)
        plt.plot(t/1e9,abs(y),'ro')
        plt.plot(t/1e9,abs(S_result),'b-')
        plt.gca().xaxis.set_major_formatter(ticker.FormatStrFormatter('%.3f'))
        plt.xlabel('freq(GHz)')
        plt.ylabel('|S21|')
        plt.legend()
        plt.subplot(223)
        plt.plot(t/1e9,np.unwrap(np.angle(y)),'ro')
        plt.plot(t/1e9,np.unwrap(np.angle(S_result)),'b-')
        plt.gca().xaxis.set_major_formatter(ticker.FormatStrFormatter('%.3f'))
        plt.xlabel('freq(GHz)')
        plt.ylabel('phase')
        plt.legend()
        plt.subplot(224)
        plt.plot([-0.5,1.5],[-0.5,1.5],'.')
        plt.xlim(0,1)
        plt.ylim(0,1)
        plt.xticks(ticks=[])
        plt.yticks(ticks=[])
        plt.text(0.5,0.9,'f = '+str(round(self.params[6]/1e9,6))+'GHz',verticalalignment='center',horizontalalignment='center')
        plt.text(0.5,0.75,'Q_int = '+str(round(self.params[6]/self.params[5]/1e3,1))+'k',verticalalignment='center',horizontalalignment='center')
        plt.text(0.5,0.6,'kappa_int = '+str(round(self.params[5]/1e3,1))+'kHz',verticalalignment='center',horizontalalignment='center')
        plt.text(0.5,0.45,'kappa_ext = '+str(round(self.params[4]/1e3,1))+'kHz',verticalalignment='center',horizontalalignment='center')
        plt.text(0.5,0.3,'delay = '+str(round(self.params[2]*1e9,1))+'ns',verticalalignment='center',horizontalalignment='center')
        plt.text(0.5,0.15,'mis-match = '+str(round(self.params[3],3)),verticalalignment='center',horizontalalignment='center')
        plt.show()
        """
        
    @property
    def error(self):
        '''standard deviation errors on the parameters '''
        kappa_error = 2*self._popt[6]*self._error[4]/self._popt[4]**2
        kappa_ext_error = 2*self._popt[6]*self._error[5]/self._popt[5]**2
        kappa_int_error = abs(kappa_error - kappa_ext_error)
        
        return [self._error[0],self._error_phase[1],self._error_phase[2],self._error[3],kappa_ext_error,kappa_int_error,self._error[6]]

    @property
    def params(self):
        '''optimized parameters '''
        kappa = self._popt[6]/abs(self._popt[4])
        kappa_ext = self._popt[6]/abs(self._popt[5])
        kappa_ext_real = kappa_ext*np.cos(self._popt[3])
        kappa_ext_imag = kappa_ext*np.sin(self._popt[3])
        kappa_int = kappa - kappa_ext_real
        return [self._popt[0]*self.A,self._popt_phase[1],self._popt_phase[2]+self.delay,self._popt[3],kappa_ext*np.exp(-1j*self._popt[3]),kappa_int,self._popt[6]]    
    

class RBM_Fit(BaseFit):
    '''Randomized Benchmarking Fit'''

    def __init__(self,data, d=2, **kw):
        '''d: d-dimensional system, for the Clifford group, d=2'''
        super(RBM_Fit, self).__init__(data=data,**kw)
        self.d = d

    def _fitfunc(self,t,A,B,p):
        y=A*p**t+B
        return y

    @property
    def p(self):
        A,B,p=self._popt
        return p

    @property
    def p_error(self):
        A_e,B_e,p_e=self._error
        return p_e

    @property
    def F(self):
        '''Fidelity '''
        d = self.d
        A,B,p=self._popt
        F=1-(1-p)*(d-1)/d
        return F

    @property
    def F_error(self):
        d = self.d
        A_e,B_e,p_e=self._error
        F_e=p_e*(1-d)/d
        return F_e


class T1_Fit(BaseFit):
    '''Fit T1'''

    def _fitfunc(self,t,A,B,T1):
        y=A*np.exp(-t/T1)+B
        return y

    @property
    def T1(self):
        A,B,T1=self._popt
        return T1

    @property
    def T1_error(self):
        A_e,B_e,T1_e=self._error
        return T1_e


class Rabi_Fit(BaseFit):
    '''Fit rabi'''

    def _fitfunc(self,t,A,B,C,lmda,Tr):
        # lmda: lambda,rabi's wavelength
        y=A*np.exp(-t/Tr)*np.cos(2*np.pi/lmda*t+B)+C
        return y

    @property
    def Tr(self):
        A,B,C,lmda,Tr = self._popt
        return Tr

    @property
    def rabi_freq(self):
        '''rabi frequency'''
        A,B,C,lmda,Tr = self._popt
        # lambda 默认单位为us, 所以返回频率为MHz
        rabi_freq=np.abs(1/lmda)
        return rabi_freq

    @property
    def rabi_freq_error(self):
        '''rabi frequency error'''
        A,B,C,lmda,Tr = self._popt
        A_e,B_e,C_e,lmda_e,Tr_e = self._error
        rabi_freq_e=np.abs(1/(lmda**2))*lmda_e
        return rabi_freq_e

    @property
    def PPlen(self):
        '''Pi Pulse Length, equal 1/2 lambda'''
        A,B,C,lmda,Tr = self._popt
        _PPlen=np.abs(lmda/2)
        return _PPlen


class Ramsey_Fit(BaseFit):
    '''Fit Ramsey'''

    def __init__(self,data,T1,**kw):
        self._T1=T1
        super(Ramsey_Fit, self).__init__(data=data,**kw)

    def _fitfunc(self,t,A,B,C,Tphi,w):
        y=A*np.exp(-t/2/self._T1-np.square(t/Tphi))*np.cos(w*t+C)+B
        return y

    @property
    def Tphi(self):
        A,B,C,Tphi,delta = self._popt
        return Tphi

    @property
    def Tphi_error(self):
        A_e,B_e,C_e,Tphi_e,delta_e=self._error
        return Tphi_e

    @property
    def detuning(self):
        A,B,C,Tphi,w = self._popt
        return w/2/np.pi


class Spinecho_Fit(BaseFit):
    '''Fit spinecho'''

    def _fitfunc(self,t,A,B,T2E):
        y=A*np.exp(-t/T2E)+B
        return y

    @property
    def T2E(self):
        A,B,T2E = self._popt
        return T2E

    @property
    def T2E_error(self):
        A_e,B_e,T2E_e=self._error
        return T2E_e
