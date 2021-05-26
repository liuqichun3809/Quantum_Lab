# -*- coding: utf-8 -*-
import numpy as np
import socket
from contextlib import contextmanager
import logging
from qulab.device import BaseDriver, QInteger, QOption, QReal, QString, QVector

log = logging.getLogger(__name__)


class Driver(BaseDriver):
    support_models = ['SLFS0218F']

    quants = [
        QReal('Frequency',
            ch=1,
            unit='Hz',
            set_cmd='FREQ %(value).13e %(unit)s',
            get_cmd='FREQ?'),
        QReal('Power',
            ch=1,
            unit='dBm',
            set_cmd='LEVEL %(value).5e %(unit)s',
            get_cmd='LEVEL?'),
        QOption('Output',
            ch=1,
            set_cmd='LEVEL:STATE %(option)s',
            options=[('OFF', 'OFF'), ('ON', 'ON')]),
        QOption('Reference',
                set_cmd='REF_10M:STATE %(option)s', 
                options=[('INT', 'EXT'), ('INT', 'EXT')]),
    ]

    CHs=[1]

    def __init__(self, addr, **kw):
        super().__init__(addr=addr, **kw)
        #self.port = kw.get('port', 2000)
        self.port = 2000

    def performOpen(self, **kw):
        try:
            IDN = self.query("*IDN?\n").split(',')
            # company = IDN[0].strip()
            model = IDN[1].strip()
            # version = IDN[3].strip()
            self.model = model
        except:
            raise IOError('query IDN error!')

    @contextmanager
    def _socket(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.addr, self.port))
            yield s

    def write(self, cmd):
        if isinstance(cmd, str):
            cmd = cmd.encode()
        with self._socket() as s:
            s.send(cmd)
            log.debug(f"{self.addr}:{self.port} << {cmd}")

    # 返回字符串格式，QReal无法用getValue
    def query(self, cmd):
        if isinstance(cmd, str):
            cmd = cmd.encode()
        with self._socket() as s:
            s.send(cmd)
            log.debug(f"{self.addr}:{self.port} << {cmd}")
            ret = s.recv(1024).decode()
            log.debug(f"{self.addr}:{self.port} >> {ret}")
            return ret