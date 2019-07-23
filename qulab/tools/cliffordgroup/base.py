import copy
import numpy as np

from qulab.tools.wavedata import *


class Gate(object):
    """docstring for Gate."""
    def __init__(self, name=None, index=None, matrix=None):
        super(Gate, self).__init__()
        self.name = name
        self.index = index
        self.matrix = matrix


class GateGroup(object):
    """docstring for GateGroup."""
    def __init__(self, gatelist=[]):
        super(GateGroup, self).__init__()
        self.namelist = []
        self.indexlist = []
        self.matrixlist = []

        for g in gatelist:
            self.namelist.append(g.name)
            self.indexlist.append(g.index)
            self.matrixlist.append(g.matrix)

    def __getitem__(self, name):
        idx = self.namelist.index(name)
        index = self.indexlist[idx]
        matrix = self.matrixlist[idx]
        return Gate(name,index,matrix)

    def genPulseByIndex(self):
        pass
