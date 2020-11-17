# -*- coding: utf-8 -*-
import numpy as np

from qulab.device import BaseDriver, QOption, QReal, QList
from qulab.tools.datafit._Fit import *


class Driver(BaseDriver):
    support_models = ['RSA5126B',]

    quants = [
        # add/select/delete general measurement view
        QOption('Add_general_measurement', set_cmd='DISP:GEN:MEAS:NEW %(option)s',
            options = [
                ('Spectrum', 'SPEC'),
                ('IQ_vs_Time', 'IQVT'),
                ('Amp_vs_Time', 'AVT'),
                ('Freq_vs_Time', 'FVT'),
                ('Pha_vs_Time', 'PHVT'),
                ('DPX', 'DPX'),
                ('TimeOverview', 'TOVerview'),
                ('SGRam', 'SGR')]),
        QOption('Select_general_measurement', set_cmd='DISP:GEN:MEAS:SEL %(option)s',
            options = [
                ('Spectrum', 'SPEC'),
                ('IQ_vs_Time', 'IQVT'),
                ('Amp_vs_Time', 'AVT'),
                ('Freq_vs_Time', 'FVT'),
                ('Pha_vs_Time', 'PHVT'),
                ('DPX', 'DPX'),
                ('TimeOverview', 'TOVerview'),
                ('SGRam', 'SGR')]),
        QOption('Delete_general_measurement', set_cmd='DISP:GEN:MEAS:DEL %(option)s',
            options = [
                ('Spectrum', 'SPEC'),
                ('IQ_vs_Time', 'IQVT'),
                ('Amp_vs_Time', 'AVT'),
                ('Freq_vs_Time', 'FVT'),
                ('Pha_vs_Time', 'PHVT'),
                ('DPX', 'DPX'),
                ('TimeOverview', 'TOVerview'),
                ('SGRam', 'SGR')]),
        QReal('Get_general_measurement', value=[], get_cmd='DISP:WIND:ACT:MEAS?'),
        
        # set spectrum analyzer parameter
        QReal('Frequency center', value=5e9, unit='Hz',
          set_cmd='SENS:SPEC:FREQ:CENT %(value)f',
          get_cmd='SENS:SPEC:FREQ:CENT?'),
        QReal('Frequency span', value=1e6, unit='Hz',
          set_cmd='SENS:SPEC:FREQ:SPAN %(value)f',
          get_cmd='SENS:SPEC:FREQ:SPAN?'),
        QOption('Points', set_cmd='SENS:SPEC:POIN:COUN %(option)s', get_cmd='SENS:SPEC:POIN:COUN?',
            options = [
                ('801', 'P801'),
                ('1601', 'P1601'),
                ('2401', 'P2401'),
                ('3201', 'P3201'),
                ('4001', 'P4001'),
                ('6401', 'P6401'),
                ('8001', 'P8001'),
                ('10401', 'P10401'),
                ('64001', 'P64001')]),
        QReal('Bandwidth', value=1e3, unit='Hz',
          set_cmd='SENS:SPEC:BAND:RES %(value)f',
          get_cmd='SENS:SPEC:BAND:RES?'),
        QReal('Acquire_Bandwidth', value=1e3, unit='Hz',set_cmd='SENS:ACQ:BAND %(value)f'),
        QOption('Acquire_mode', set_cmd='SENS:ACQ:MODE %(option)s',
            options = [
                ('samples', 'SAMP'),
                ('length', 'LENG')]),
        QReal('Acquire_length', value=1e-3, unit='s',
          set_cmd='SENS:ACQ:SEC %(value)f',
          get_cmd='SENS:ACQ:SEC?'),
        QReal('Analysis_length', value=1e-3, unit='s',
          set_cmd='SENS:ANAL:LENG %(value)f',
          get_cmd='SENS:ANAL:LENG?'),
        QReal('Spectrum_length', value=1e-3, unit='s',
          set_cmd='SENS:SPEC:LENG %(value)f',
          get_cmd='SENS:SPEC:LENG?'),
        QOption('IQ_points', set_cmd='SENS:IQVT:MAXT %(option)s',
            options = [
                ('1k', 'ONEK'),
                ('10k', 'TENK'),
                ('100k', 'HUND'),
                ('max', 'NEV')]),
        QOption('Mode', set_cmd='INIT:CONT %(option)s', get_cmd='INIT:CONT?',
            options = [
                ('Continus', 'ON'),
                ('Single', 'OFF')]),
        
        # get spectrum trace and I/Q trace
        QReal('Spectrum_trace', value=[], unit='dBm', ch=1, get_cmd='FETCh:SPECtrum:TRACe%(ch)d?'),
        QReal('I_trace', value=[], unit='V', get_cmd='FETC:IQVT:I?'),
        QReal('Q_trace', value=[], unit='V', get_cmd='FETC:IQVT:Q?'),
        QReal('Amp_trace', value=[], unit='V', get_cmd='FETC:AVT?'),
        QReal('Freq_trace', value=[], unit='Hz', get_cmd='FETC:FVT?'),
    ]

    
    def init(self):
        self.write('SYSTem:PRESet')

    def performSetValue(self, quant, value, **kw):
        if quant.name == '':
            return
        else:
            return BaseDriver.performSetValue(self, quant, value, **kw)
        
    def performGetValue(self, quant, **kw):
        if quant.name in ['Spectrum_trace','I_trace','Q_trace','Amp_trace','Freq_trace']:
            if '%(ch)d' in quant.get_cmd:
                get_cmd = quant.get_cmd % dict(ch=quant.ch)
            else:
                get_cmd = quant.get_cmd
            value = self.query_binary_values(get_cmd)
        else:
            value = quant.getValue()
        return value
    
    def get_spectrum_trace(self, timeout=10):
        self.set_timeout(timeout)
        self.ins.write('INIT')
        center = self.getValue('Frequency center')
        span = self.getValue('Frequency span')
        points = int(self.getValue('Points')[1:])
        freq = np.linspace(center-span/2, center+span/2, points)
        spectrum = self.getValue('Spectrum_trace', ch=1)
        return [freq, spectrum]
    
    def get_IQ_trace(self):
        self.setValue('Add_general_measurement', 'Freq_vs_Time')
        freq = np.average(self.getValue('Freq_trace'))
        I = self.getValue('I_trace')
        Q = self.getValue('Q_trace')
        time_list = np.linspace(1,len(I),len(I))/5
        fit = Sin_Fit((time_list,I))
        A, B, w, phi = fit._popt
        #print(freq)
        #print(0.5*w/np.pi)
        time_list = time_list*(0.5*w/np.pi/freq)
        return [time_list, I, Q]
