from qulab.device import BaseDriver, QInteger, QOption, QReal, QVector
from . import spi_read_write


class Driver(BaseDriver):

    CHs=[1,2,3,4,5,6,7,8,9,10,11,12]
    quants = [
        QReal('Offset',value=0.0,unit='V',ch=1,),]

    def __init__(self, **kw):
        super().__init__(**kw)
        
    def __del__(self):
        self.handle.disconnect()

    def performOpen(self):
        self.handle = spi_read_write.SpiControl()
        self.handle.connect(self.addr)
        self.handle.spi_set_config()
        super().performOpen()

    def performClose(self):
        self.handle.disconnect()
        super().performClose()
        
    def performSetValue(self, quant, value, ch=1, **kw):
        if quant.name == 'Offset':
            self.handle.spi_set_config()
            self.handle.spi_set_voltage(ch, value)