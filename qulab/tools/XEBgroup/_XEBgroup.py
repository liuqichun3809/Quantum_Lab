import numpy as np
from functools import reduce

from .base import GateGroup,Gate
from qulab.tools.wavedata import *


class xebgroup(GateGroup):
    """docstring for XEBGroup."""
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
        [ [ 1, 0], [ 0, 1] ],
        [ [ 1, 0, 0, 0], [ 0, 1, 0, 0], [ 0, 0, 1, 0], [ 0, 0, 0, -1] ],
        [ [ 1, 0, 0, 0], [ 0, 1/np.sqrt(2), 1j/np.sqrt(2), 0], [ 0, 1j/np.sqrt(2), 1/np.sqrt(2), 0], [ 0, 0, 0, 1] ],
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
                            ['Delay'],
                            ['cPhase'],
                            ['iSWAP'],
                        ]
    # name为序号,第24对应为‘Delay'，不参与随机序列生成，只是作为两比特操作时对应xy脉冲的等待
    # 第25和26对应为待标定的两比特们操作，不参与随机序列生成
    namelist_clifford_singlequbit=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26]

    def __init__(self):
        self.namelist = self.namelist_clifford_singlequbit
        self.indexlist = self.indexlist_clifford_singlequbit
        self.matrixlist = list(self.matrixlist_clifford_singlequbit) #需要转化为列表格式

    def seq_mat(self,nlist1,nlist2,target=25):
        '''根据序号列计算操作矩阵'''
        I = np.eye(2)
        U = np.eye(4)
        nl1=list(nlist1)
        nl2=list(nlist2)
        for idx in range(len(nl1)):
            temp_U = np.kron(I, self.matrixlist[nl1[idx]])
            U = np.dot(temp_U, U)
            temp_U = np.kron(self.matrixlist[nl2[idx]], I)
            U = np.dot(temp_U, U)
            U = np.dot(self.matrixlist[target], U)
        return U

    def random(self,size,group=None,ref=24):
        '''随机单比特操作序号列表,待标定的门操作对应单比特门固定为Delay'''
        #group 是要随机Clifford门的序号列表，注意不包含第24、25、26个门操作
        if group is None:
            group = self.namelist[0:-4]
        res=np.array([])
        for i in range(int(size)):
            _r=np.append(np.random.choice(group,1), ref)
            res=np.append(res, _r).astype(np.int32)
        return list(res)

    def gen_seq(self,nlist,reduce_flag=True):
        '''根据序号列表生成索引序列'''
        nl=list(nlist)
        if reduce_flag:
            index_seq=reduce(np.append,[self.indexlist[i] for i in nl])
        else:
            index_seq=[self.indexlist[i] for i in nl]
        return index_seq

    def xeb_seq(self,size,group=None,target=25):
        '''产生RBM索引序列,ref是需要标定的门序号，空则对应为参考序列'''
        l1=self.random(size,group,ref=24) #给qubit1的门序列
        l2=self.random(size,group,ref=24) #给qubit2的门序列
        l3=reduce(np.append,np.vstack([l1[0:-2:2],l2[0:-2:2],l1[1:-1:2]]).T) #合并的序列
        seq1=self.gen_seq(l1)
        seq2=self.gen_seq(l2)
        seq3=self.gen_seq(l3,reduce_flag=False)
        mat=self.seq_mat(l1,l2,target=25)
        mat=np.dot(mat,np.array([[1,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]]))
        prob_array = np.abs(np.diag(np.dot(mat, mat.conj().T)))
        return seq1, seq2, seq3, prob_array

    @staticmethod
    def gen_XY(index, pi_len, pi_factor, half_pi_len, half_pi_factor, cp_len, cp_factor, sRate, TYPE=Gaussian2):
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
                    pulse_wd_IQ=1j*pi_factor*TYPE(pi_len,sRate)
        else:
                if index[0]=='X':
                    if index[2]=='p':
                        pulse_wd_IQ=half_pi_factor*TYPE(half_pi_len,sRate)
                    else:
                        pulse_wd_IQ=-half_pi_factor*TYPE(half_pi_len,sRate)
                elif index[0]=='Y':
                    if index[2]=='p':
                        pulse_wd_IQ=1j*half_pi_factor*TYPE(half_pi_len,sRate)
                    else:
                        pulse_wd_IQ=-1j*half_pi_factor*TYPE(half_pi_len,sRate)
                else:
                    pulse_wd_IQ=Blank(cp_len,sRate)
        return pulse_wd_IQ
    
    @staticmethod
    def gen_Z(index, pi_len, pi_factor, half_pi_len, half_pi_factor, cp_len, cp_factor, sRate, TYPE=DC):
        '''通过给定的索引和相关参数，产生相应的波形脉冲；
        index : I/X/Y/X2p/X2n/Y2p/Y2n
        TYPE : 为由 width，sRate 两个参数决定的Wavedata类波形，参考Wavedata模块(如: DC,Gaussian,Gaussian2,CosPulse)
        '''
        if len(index)==1:
            pulse_wd_IQ=Blank(pi_len,sRate)
        elif index[0]=='D':
            pulse_wd_IQ=cp_factor*TYPE(cp_len,sRate)
        return pulse_wd_IQ
    
    
    def xeb_wd(self, indexseq, pi_array, cp_array, sRate, buffer=0, TYPE=Gaussian2, drag_ratio=0):
        '''根据索引序列产生波形序列'''
        pi_len, pi_factor, half_pi_len, half_pi_factor = pi_array
        cp_len, cp_factor = cp_array
        res_wd=Wavedata(sRate=sRate)
        buffer_wd=Blank(buffer,sRate)
        for v in indexseq:
            XY_wd=self.gen_XY(v,pi_len,pi_factor,half_pi_len,half_pi_factor,cp_len,cp_factor,sRate,TYPE)
            amp=np.max(np.abs(XY_wd.data))
            XY_wd_drag=XY_wd.derivative()
            # 将DRAG幅度用MHz表示，以便后续计算DRAG系数a，通常即为（拉比频率/非谐性）
            XY_wd_drag=1e-6*XY_wd_drag
            XY_wd=XY_wd+1j*XY_wd_drag*drag_ratio
            res_wd=res_wd|XY_wd|buffer_wd
        return res_wd
