import logging
import time
import numpy as np
import re
from threading import Thread

from qulab.device import BaseDriver, QInteger, QOption, QReal, QString, QVector
from .x6api import X6api

log = logging.getLogger('qulab.Driver')
x6 = X6api()

class Driver(BaseDriver):
    support_models = ['X6_1000',]
    quants = []
    def __init__(self, addr=None, **kw):
        super().__init__(addr=addr,**kw)
        self.trig_n = 100
        self.deviceID = 0
        self.model = 'X6_1000M'
        self.config = dict(ref_clk_source = 'EXTERNAL',
                           sample_clk_source = 'EXTERNAL',
                           trig_source = 'EXTERNAL',
                           adc_inchannel = [1,1],
                           n=1024,
                           repeats=512,
                           sampleRate=1e9,
                           ARange=1.0,
                           BRange=1.0,
                           triggerDelay=0,
                           triggerTimeout=0,
                           dac_outchannel = [1,1,1,1],
                           dac_sRate=0.5e9)

    def performOpen(self):
        if self.addr is not None:
            dict_parse=self._parse_addr(self.addr)
        else:
            dict_parse={}
        self.model=dict_parse.get('model',None)
        deviceID=dict_parse.get('deviceID',0) #default 0
        self.deviceID = deviceID
        x6.Open(self.deviceID)
        
    def _parse_addr(self,addr):
        x6_addr = re.compile(
            r'^X6_(1000M|500M)::DEVICE::([0-9]+)(|::INSTR)$')
        # example: X6_1000M::DEVICE::0
        m = x6_addr.search(addr)
        if m is None:
            raise Error('X6_1000M address error!')
        model = 'X6_'+str(m.group(1))
        deviceID = int(m.group(2))
        return dict(model=model,deviceID=deviceID)
    
    def performClose(self, **kw):
        x6.Close()
    
    # according the input config dict, set X6 paras
    def set_para(self,**config):
        self.config.update(config)
        self.set_board_para()
        self.set_adc_para()
        self.set_dac_para()
        self.set_adc_delay()
    
    def set_board_para(self):
        if self.config['ref_clk_source'] == 'EXTERNAL':
            x6.set_ReferenceClockSource(0) # 0 for external
        else:
            x6.set_ReferenceClockSource(1)
        if self.config['sample_clk_source'] == 'EXTERNAL':
            x6.set_SampleClockSource(0) # 0 for external
        else:
            x6.set_SampleClockSource(1)
        if self.config['trig_source'] == 'EXTERNAL':
            x6.set_ExternalTrigger(1) # 1 for external trigger true
        else:
            x6.set_ExternalTrigger(0)  
    
    def set_adc_para(self):
        x6.set_AdcRate(self.config['sampleRate']/1e6)
        x6.set_AdcActiveChannel(self.config['adc_inchannel'])
        x6.set_AdcFrameSize(self.config['n'])
        x6.set_AdcRepeats(self.config['repeats'])
        
    def set_dac_para(self):
        x6.set_DacRate(self.config['dac_sRate']/1e6)
        x6.set_DacActiveChannel(self.config['dac_outchannel'])
        
    def write_dac_wavedata(self,wavedata):
        #x6.StartStreaming()
        #x6.EnterPatternMode()
        x6.write_dac_wavedata(wavedata=wavedata)
        #x6.PatternLoadCommand()
        #x6.StopStreaming()
        
    # there is still some bug with this function
    def set_acquire_adc_data_timeout(time_limited): # the timeout unit is 's'
        def wrapper(func):
            def __wrapper(params):
                class TimeLimited(Thread):
                    def __init__(self):
                        Thread.__init__(self)
                    def run(self):
                        func(params)
                    def _stop(self):
                        if self.is_alive():
                            Thread._Thread__stop(self)
                            raise Exception('Function execution overtime')
                t = TimeLimited()
                t.start()
                t.join(timeout=time_limited)
                if t.is_alive():
                    t._stop()
                    raise Exception('Function execution overtime')
            return __wrapper
        return wrapper
    
    #@set_acquire_adc_data_timeout(10) # the timeout unit is 's'
    def acquire_adc_data(self):
        x6.StopStreaming()
        x6.StartStreaming()
        #x6.do_trigger(trig_n=self.trig_n) #only for manual soft trigger test
        time.sleep(self.config['repeats']/200)
        data = np.array(x6.read_adc_data())
        data = data.reshape(self.config['repeats']*2,self.config['n']+16)
        ch_A = np.zeros((self.config['repeats'],self.config['n']))
        ch_B = np.zeros((self.config['repeats'],self.config['n']))
        idx = 0
        for record in data:
            if record[3] == 1:
                ch_A[int(idx/2),:] = record[14:-2]
            else:
                ch_B[int(idx/2),:] = record[14:-2]
            idx = idx+1
        return ch_A,ch_B
    
    def set_adc_delay(self):
        x6.write_wishbone_register(baseAddr=2048, offset=3, data=int(self.config['triggerDelay']/4*16))
    
    def ManualTrigger(self, trig):
        x6.ManualTrigger(state=trig)
    
    def StartStreaming(self):
        x6.StartStreaming()
        
    def StopStreaming(self):
        x6.StopStreaming()
    
    def EnterPatternMode(self):
        x6.EnterPatternMode()
        
    def LeavePatternMode(self):
        x6.LeavePatternMode();
    
    def PatternLoadCommand(self):
        x6.PatternLoadCommand()
        
    def read_adc_data(self):
        return x6.read_adc_data()
    
    # only for manual soft trigger test
    def do_trigger(self,trig_n=0):
        x6.do_trigger(trig_n=trig_n)  
    
    def get_temperature(self):
        return x6.Temperature()
    
    def write_WB(self, baseAddr, offset, data):
        x6.write_wishbone_register(baseAddr=baseAddr,offset=offset, data=data)
        
    def read_WB(self, baseAddr, offset):
        return x6.read_wishbone_register(baseAddr=baseAddr, offset=offset)
    