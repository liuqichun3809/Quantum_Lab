import numpy as np
from functools import reduce

from .base import GateGroup,Gate
from qulab.tools.wavedata import *


class cliffordGroup(GateGroup):
    """docstring for cliffordGroup."""
    # clifford门的矩阵表示
    matrixlist_clifford_singlequbit=np.array([
        [ [  1,  0] , [  0, 1] ],
        [ [  0,-1j] , [-1j, 0] ],
        [ [  0, -1] , [  1, 0] ],
        [ [-1j,  0] , [  0,1j] ],

        [ [1/np.sqrt(2), -1j/np.sqrt(2)] , [-1j/np.sqrt(2), 1/np.sqrt(2)] ],
        [ [1/np.sqrt(2),  1j/np.sqrt(2)] , [ 1j/np.sqrt(2), 1/np.sqrt(2)] ],
        [ [1/np.sqrt(2),  -1/np.sqrt(2)] , [  1/np.sqrt(2), 1/np.sqrt(2)] ],
        [ [1/np.sqrt(2),   1/np.sqrt(2)] , [ -1/np.sqrt(2), 1/np.sqrt(2)] ],
        [ [1/np.sqrt(2)-1j/np.sqrt(2),0] , [0,1/np.sqrt(2)+1j/np.sqrt(2)] ],
        [ [1/np.sqrt(2)+1j/np.sqrt(2),0] , [0,1/np.sqrt(2)-1j/np.sqrt(2)] ],

        [ [-1j/np.sqrt(2),-1j/np.sqrt(2)] , [-1j/np.sqrt(2), 1j/np.sqrt(2)] ],
        [ [ 1j/np.sqrt(2),-1j/np.sqrt(2)] , [-1j/np.sqrt(2),-1j/np.sqrt(2)] ],
        [ [-1j/np.sqrt(2), -1/np.sqrt(2)] , [  1/np.sqrt(2), 1j/np.sqrt(2)] ],
        [ [ 1j/np.sqrt(2), -1/np.sqrt(2)] , [  1/np.sqrt(2),-1j/np.sqrt(2)] ],
        [ [0,-1/np.sqrt(2)-1j/np.sqrt(2)] , [1/np.sqrt(2)-1j/np.sqrt(2), 0] ],
        [ [0,-1/np.sqrt(2)+1j/np.sqrt(2)] , [1/np.sqrt(2)+1j/np.sqrt(2), 0] ],

        [ [ 0.5-0.5j, -0.5-0.5j ],  [  0.5-0.5j,  0.5+0.5j ] ],
        [ [ 0.5+0.5j, -0.5+0.5j ],  [  0.5+0.5j,  0.5-0.5j ] ],
        [ [ 0.5+0.5j,  0.5-0.5j ],  [ -0.5-0.5j,  0.5-0.5j ] ],
        [ [ 0.5-0.5j,  0.5+0.5j ],  [ -0.5+0.5j,  0.5+0.5j ] ],
        [ [ 0.5-0.5j,  0.5-0.5j ],  [ -0.5-0.5j,  0.5+0.5j ] ],
        [ [ 0.5+0.5j,  0.5+0.5j ],  [ -0.5+0.5j,  0.5-0.5j ] ],
        [ [ 0.5+0.5j, -0.5-0.5j ],  [  0.5-0.5j,  0.5-0.5j ] ],
        [ [ 0.5-0.5j, -0.5+0.5j ],  [  0.5+0.5j,  0.5+0.5j ] ],
    ])
    # 分解的门的索引
    indexlist_clifford_singlequbit=[
                            ['I'],
                            ['X'],
                            ['Y'],
                            ['Y','X'],

                            ['X2p'],
                            ['X2n'],
                            ['Y2p'],
                            ['Y2n'],
                            ['X2n','Y2p','X2p'],
                            ['X2n','Y2n','X2p'],

                            ['X','Y2n'],
                            ['X','Y2p'],
                            ['Y','X2p'],
                            ['Y','X2n'],
                            ['X2p','Y2p','X2p'],
                            ['X2n','Y2p','X2n'],

                            ['Y2p','X2p'],
                            ['Y2p','X2n'],
                            ['Y2n','X2p'],
                            ['Y2n','X2n'],
                            ['X2p','Y2n'],
                            ['X2n','Y2n'],
                            ['X2p','Y2p'],
                            ['X2n','Y2p'],
                        ]
    # name为序号
    namelist_clifford_singlequbit=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23]

    def __init__(self):
        self.namelist = self.namelist_clifford_singlequbit
        self.indexlist = self.indexlist_clifford_singlequbit
        self.matrixlist = list(self.matrixlist_clifford_singlequbit) #需要转化为列表格式

    @staticmethod
    def matrix_compare(a, b, phase=True):
        '''比较a,b两个矩阵是否相等'''
        if phase: # 考虑不同相位
            result=any([np.where(abs(f*a-b)<1e-5, True, False).all() for f in [1,-1,1j,-1j]])
        else:
            result=np.where(abs(a-b)<1e-5, True, False).all()
        return result

    def find_number(self, a):
        '''查找a矩阵在matrixlist中的序号'''
        for i,v in enumerate(self.matrixlist):
            if self.matrix_compare(a, v, phase=True):
                return i

    def inverse_number(self,nlist):
        '''根据序号列表找出反转的矩阵序号'''
        nl=list(nlist)
        mat=reduce(np.dot, [self.matrixlist[i] for i in reversed(nl)])
        mat_inv=np.array(np.matrix(mat).H)
        inv_n=self.find_number(mat_inv)
        return inv_n

    def random(self,size,group=None,ref=[]):
        '''随机不包含反转门的序号列表'''
        #group 是要随机Clifford门的序号列表
        if group is None:
            group = self.namelist
        # i_r=list(np.random.choice(group,size=int(size)))
        res=np.array([])
        for i in range(int(size)):
            _r=np.append(np.random.choice(group,1), ref)
            res=np.append(res, _r).astype(np.int32)
        return list(res)

    def gen_seq(self,nlist):
        '''根据序号列表生成索引序列'''
        nl=list(nlist)
        index_seq=reduce(np.append,[self.indexlist[i] for i in nl])
        return index_seq

    def rbm_seq(self,size,group=None,ref=[]):
        '''产生RBM索引序列,ref是需要标定的门序号，空则对应为参考序列'''
        l1=self.random(size,group,ref)
        l2=self.inverse_number(l1)
        l1.append(l2)
        seq=self.gen_seq(l1)
        return seq

    def check_seq(self, seq):
        '''检查索引序列的矩阵乘积是否归一化'''
        kw={'I':0, 'X':1, 'Y':2, 'X2p':4, 'X2n':5, 'Y2p':6, 'Y2n':7}
        idxs=[kw[i] for i in seq]
        check_mat=reduce(np.dot,[self.matrixlist[i] for i in reversed(idxs)])
        res = self.matrix_compare(check_mat,self.matrixlist[0],phase=True)
        return res

    @staticmethod
    def gen_XY(index, pi_len, pi_factor, half_pi_len, half_pi_factor, sRate, TYPE=Gaussian2):
        '''通过给定的索引和相关参数，产生相应的波形脉冲；
        index : I/X/Y/X2p/X2n/Y2p/Y2n
        TYPE : 为由 width，sRate 两个参数决定的Wavedata类波形，参考Wavedata模块(如: DC,Gaussian,Gaussian2,CosPulse)
        '''
        if len(index)==1:
                if index=='I':
                    pulse_wd_IQ=Blank(pi_len,sRate)
                elif index=='X':
                    pulse_wd_IQ=pi_factor*TYPE(pi_len,sRate)
                elif index=='Y':
                    pulse_wd_IQ=-1j*pi_factor*TYPE(pi_len,sRate)
        else:
                if index[0]=='X':
                    if index[2]=='p':
                        pulse_wd_IQ=half_pi_factor*TYPE(half_pi_len,sRate)
                    else:
                        pulse_wd_IQ=-half_pi_factor*TYPE(half_pi_len,sRate)
                elif index[0]=='Y':
                    if index[2]=='p':
                        pulse_wd_IQ=-1j*half_pi_factor*TYPE(half_pi_len,sRate)
                    else:
                        pulse_wd_IQ=1j*half_pi_factor*TYPE(half_pi_len,sRate)
        return pulse_wd_IQ

    def rbm_wd(self, indexseq, pi_array, sRate, buffer=0, TYPE=Gaussian2, check=False):
        '''根据索引序列产生波形序列'''
        if check:
            assert self.check_seq(indexseq)
        pi_len, pi_factor, half_pi_len, half_pi_factor = pi_array
        res_wd=Wavedata(sRate=sRate)
        buffer_wd=Blank(buffer,sRate)
        for v in indexseq:
            XY_wd=self.gen_XY(v,pi_len,pi_factor,half_pi_len,half_pi_factor,sRate,TYPE)
            res_wd=res_wd|XY_wd|buffer_wd
        return res_wd
    
    def rbm_wd_drag(self, indexseq, pi_array, sRate, buffer=0, TYPE=Gaussian2, check=False):
        '''根据索引序列产生波形序列'''
        if check:
            assert self.check_seq(indexseq)
        pi_len, pi_factor, half_pi_len, half_pi_factor = pi_array
        res_wd=Wavedata(sRate=sRate)
        buffer_wd=Blank(buffer,sRate)
        for v in indexseq:
            XY_wd=self.gen_XY(v,pi_len,pi_factor,half_pi_len,half_pi_factor,sRate,TYPE)
            amp=np.max(np.abs(XY_wd.data))
            XY_wd=XY_wd.derivative()
            # 将DRAG幅度用MHz表示，以便后续计算DRAG系数a，通常即为（拉比频率/非谐性）
            XY_wd=1e-6*XY_wd
            #if 'n' in v:
            #    XY_wd = -XY_wd
            res_wd=res_wd|XY_wd|buffer_wd
        return res_wd
