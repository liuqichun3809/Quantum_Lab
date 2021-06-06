from qulab.device import BaseDriver, QInteger, QOption, QReal, QVector
from . import Trigboard


class Driver(BaseDriver):

    CHs=[1,2,3,4,5,6,7,8]
    """ch=0表示所有通道"""
    quants = [
        QReal('Freq',value=2.5e3,unit='Hz',ch=0,),
        QReal('Width',value=5e-6,unit='s',ch=0,),
        QReal('Delay',value=0,unit='ps',ch=0,),
        QInteger('Count',value=0,ch=0,),
        ]

    def __init__(self, **kw):
        super().__init__(**kw)
        
    def __del__(self):
        self.handle.disconnect()

    def performOpen(self):
        self.handle = Trigboard.TrigBoard()
        self.handle.connect(self.addr)
        self.handle.config_clock(ref_clock='10MHz')
        self.setTrigSource(trig_source='int')
        super().performOpen()

    def performClose(self):
        self.handle.disconnect()
        super().performClose()

    def setTrigSource(self,trig_source='int'):
        if 'int' in trig_source or 'INT' in trig_source:
            self.handle.trig_switch_int()
        else:
            self.handle.trig_switch_ext()
    
    def setTrig(self,freq=2.5e3,width=5e-6,delay=0,count=0,ch=0):
        """"
        freq为trig频率，单位Hz；
        width为trig脉宽，单位s，若设置为0表示50%占空比；
        delay为通道延时，单位ps；
        count为trig次数，最少为2次，设置为0表示连续输出；
        ch为通道编号，从1开始，设置为0表示所有通道；
        """
        self.handle.set_internal_trig(channel=ch, freq=freq, offet_time =delay, count=count, width=width)
        self.handle.start_internal_trig()
        # 记录设置的参数
        self.quants[0].value=freq
        self.quants[0].ch=ch
        self.quants[1].value=width
        self.quants[1].ch=ch
        self.quants[2].value=delay
        self.quants[2].ch=ch
        self.quants[3].value=count
        self.quants[3].ch=ch
        for q in self.quants:
            self._add_quant(q)
    
    def performSetValue(self, quant, value, ch=1, **kw):
        if quant.name == 'Freq':
            width = self.quantities['Width'].getValue()
            self.setFreqAndWidth(value,width,ch)
        elif quant.name == 'Width':
            freq = self.quantities['Freq'].getValue()
            self.setFreqAndWidth(freq,value,ch)
        elif quant.name == 'Delay':
            self.handle.set_trig_offset(ch, value)
        elif quant.name == 'Count':
            self.handle.set_trig_count(ch, value)
                
    def setFreqAndWidth(self,freq,width,ch):
        self.handle.set_trig_freq(channel=ch, freq=freq, width=width)