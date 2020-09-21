import numpy as np
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
