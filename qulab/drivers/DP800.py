# -*- coding: utf-8 -*-
import numpy as np

from qulab.device import BaseDriver, QInteger, QOption, QReal, QString, QVector


class Driver(BaseDriver):

    support_models = ['DP832']
    '''Rigol DP800 series DC source'''

    quants = [
        QReal('Offset', value=0, unit='V', ch=1,
          set_cmd=':SOUR%(ch)d:VOLT %(value).2f',
          get_cmd=':SOUR%(ch)d:VOLT?'),

         QOption('Output', ch=1,
           set_cmd=':OUTP CH%(ch)d,%(option)s',
           get_cmd=':OUTP? CH%(ch)d',
           options=[('OFF', 'OFF'), ('ON', 'ON')]),
    ]
