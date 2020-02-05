from sympy import *
import numpy as np


class MLE(object):
    def __init__(self):
        # qubit 位数
        self._N = 1
        self._K = None
        self._T = None

    def set_T(self):
        # 构建Symbol形式的矩阵T，用于生成密度矩阵，保证密度矩阵半正定和迹为1的特性
        self._T = np.tril(np.zeros([2**self._N, 2**self._N]))*Symbol('t')
        self._Tc = np.tril(np.zeros([2**self._N, 2**self._N]))*Symbol('t')
        for idx in range(4**self._N):
            t = Symbol('t'+str(idx))
            tc = Symbol('t'+str(idx))
            row = np.sqrt(idx)
            col = (idx-(int(row))**2)//2
            if (idx-(int(row))**2)%2==1:
                t *= 1j
                tc *= -1j
            self._T[int(row)][col] += t    
            self._Tc[col][int(row)] += tc  
        return self
    
    def set_density_maritx(self):
        # 通过矩阵T生成密度矩阵
        self.set_T()
        self.density_M = np.dot(self._T, self._Tc)
        self.density_M = self.density_M/self.density_M.trace()
        return self.density_M
    
    def get_U(self, qubit_idx=0, pre_operation='I'):
        # 本征态定义为 |qN ... q2 q1 q0> 形式（如|000>,|001>,|010>...）
        # qubit_idx表示qubit序号，按照本征态定义中的N到0顺序排列
        # pre_operation可选为 'I', 'X2p', 'Y2p'中的一种，分别表示不操作、绕x轴转+pi/2、绕y轴转+pi/2
        # 本征态矢量定义为 [|000>,
        #             |001>,
        #             |010>,
        #             |011>,
        #             |100>,
        #             |101>,
        #             |110>,
        #             |111>,
        #              .
        #              .
        #              .]
        I = np.eye(2)
        X2p = self.get_R_x(theta=np.pi/2)
        X = self.get_R_x(theta=np.pi)
        Y2p = self.get_R_y(theta=np.pi/2)
        if pre_operation=='I':
            U = I
        elif pre_operation=='X2p':
            U = X2p
        elif pre_operation=='X':
            U = X
        elif pre_operation=='Y2p':
            U = Y2p
        else:
            raise ValueError('the "pre_operation" is illegal')
        
        for n in range(self._N-qubit_idx-1):
            U = np.kron(I, U)
        for n in range(qubit_idx):
            U = np.kron(U, I)
        return U
    
    def set_likelihood_func(self, meas_pre_operation, meas_data):
        ## 输入参数 meas_pre_operation 为shape=[self._N, 4**self._N-1]的矩阵，元素为str类型，可选为 'I', 'X2p', 'Y2p'中的一种
        # 第 i 行表示对qubit i的操作
        # N行的每一列组合起来表示一次测量中对N个qubit的预操作组合，所以共有4**self._N-1种预操作（测量）
        
        ## 输入参数 meas_data 为shape=[2,2**self._N]或者shape=[1,2**self._N]的矩阵，元素为数值
        # 此时每一列表示meas_pre_operation预操作下的测量结果，两者顺序是一一对应的
        
        # 根据预操作矩阵的行数设置qubit个数
        self._N = len(meas_pre_operation)
        # 生成符号型的密度矩阵
        self.set_density_maritx()
        # 初始化likelihood function
        self.likelihood_func = 0
        for op_idx in range(len(meas_pre_operation[0])):
            # 根据每一组预操作获得对应的算符矩阵U
            U = np.eye(2**self._N)
            for q_idx in range(self._N):
                temp_U = self.get_U(qubit_idx = q_idx, pre_operation = meas_pre_operation[q_idx][op_idx])
                U = np.dot(temp_U, U)
            # 对每一组测量结果计算得到likelihood_func的一项，再对所有测量结果进行累加，获得likelihood_func
            temp = np.dot(U, self.density_M)
            temp = np.dot(temp, U.conj().T)
            prob0_m = np.abs(np.diag(temp))
            for p_idx in range(4):
                self.likelihood_func += meas_data[p_idx][op_idx]*log(prob0_m[p_idx])
        self.likelihood_func = simplify(self.likelihood_func)
        return self.likelihood_func
    
    def get_R_x(self, theta):
        R_x = np.zeros([2,2])*1j
        R_x[0][0] = np.cos(theta/2)
        R_x[1][1] = np.cos(theta/2)
        R_x[0][1] = -1j*np.sin(theta/2)
        R_x[1][0] = -1j*np.sin(theta/2)
        return R_x
    
    def get_R_y(self, theta):
        R_y = np.zeros([2,2])*1j
        R_y[0][0] = np.cos(theta/2)
        R_y[1][1] = np.cos(theta/2)
        R_y[0][1] = -np.sin(theta/2)
        R_y[1][0] = np.sin(theta/2)
        return R_y