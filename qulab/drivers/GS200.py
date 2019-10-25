# -*- coding: utf-8 -*-
import numpy as np

from qulab.device import BaseDriver, QInteger, QOption, QReal, QString, QVector


class Driver(BaseDriver):
    support_models = ['GS200']

    quants = [
        QOption('Mode',
           set_cmd=':SOUR:FUNC %(option)s',
           get_cmd=':SOUR:FUNC?',
           options=[('voltage', 'VOLT'), ('current', 'CURR')]),
        
        QOption('Range',
           set_cmd=':SOUR:RANG %(option)s',
           get_cmd=':SOUR:RANG?',
           options=[('0.001', 1E-3), ('0.01', 10E-3), 
                    ('0.1', 100E-3), ('0.2', 200E-3), 
                    ('1', 1E+0), ('10', 10E+0),
                    ('30', 30E+0)]),
        
        QReal('Level', value=0, unit='V or A',
          set_cmd=':SOUR:LEV %(value).8f',
          get_cmd=':SOUR:LEV?'),
        
        QReal('LevelAuto', value=0, unit='V or A',
          set_cmd=':SOUR:LEV:AUTO %(value).8f',
          get_cmd=':SOUR:LEV?'),
        
        QReal('ProtectVolt', value=0, unit='V',
          set_cmd=':SOUR:PROT:VOLT %(value)d',
          get_cmd=':SOUR:PROT:VOLT?'),
        
        QReal('ProtectCurr', value=0, unit='A',
          set_cmd=':SOUR:PROT:CURR %(value).8f',
          get_cmd=':SOUR:PROT:CURR?'),

         QOption('Output',
           set_cmd=':OUTP %(option)s', options=[('OFF', 'OFF'), ('ON', 'ON')]),
    ]
