from qulab.device import BaseDriver, QInteger, QOption, QReal, QVector
from . import AWGboard


class Driver(BaseDriver):
    support_models = ['MF_AWG',]

    CHs=[1,2,3,4]
    quants = [
        QReal('Offset',value=0,unit='V',ch=1,),
        QReal('Amplitude',value=1,unit='V',ch=1,),
        QInteger('Output',value=0,ch=1,),
        ]

    def __init__(self, **kw):
        super().__init__(**kw)
        
    def __del__(self):
        self.handle.disconnect()

    def performOpen(self):
        self.handle = AWGboard.AWGBoard()
        self.handle.connect(self.addr)
        self.handle.InitBoard()
        self._output_status = [0, 0, 0, 0]
        super().performOpen()

    def performClose(self):
        self.handle.disconnect()
        super().performClose()

    def performSetValue(self, quant, value, ch=1, **kw):
        if quant.name == 'Offset':
            self.setOffset(value, ch)
        elif quant.name == 'Amplitude':
            self.setVpp(value,ch)
        elif quant.name == 'Output':
            if value==1:
                self.on(ch)
            elif value==0:
                self.off(ch)
            else:
                raise Error('Wrong Value!')

    def on(self, ch=1):
        self.handle.Start(ch)
        self._output_status[ch - 1] = 1

    def off(self, ch=1):
        self.handle.Stop(ch)
        self._output_status[ch - 1] = 0

    def setWaveform(self,
                    points,
                    mark=[],
                    ch=1,
                    wtype='trig',
                    delay=0,
                    is_continue=False):
        if len(mark):
            self.handle.mark_is_in_wave = True
        else:
            self.handle.mark_is_in_wave = False
        wlist = [self.handle.gen_wave_unit(points, wtype, delay, mark)]
        self.handle.wave_compile(ch, wlist, is_continue=is_continue)
        for index, on in enumerate(self._output_status):
            if on:
                self.handle.Start(index + 1)

    def setVpp(self, vpp, ch=1):
        vpp = min(abs(vpp), 1.351)
        volt = 1.351
        gain = vpp / volt
        self.handle.set_channel_gain(ch, gain)
        self.handle._SetDACMaxVolt(ch, volt)

    def setOffset(self, offs, ch=1):
        self.handle.SetOffsetVolt(ch, offs)
