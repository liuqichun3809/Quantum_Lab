import re
import numpy as np
import matplotlib.pyplot as plt


class GSS(object):
    def __init__(self):
        # 输入gate_list格式类似为 ['X0','X1','Y2p1',['X2n0','Y2'],'S0_1','CP1_2','S0_1:2','CP1_2:3','G0_1']
        # 其中内部的 [ ] 内门操作表示为同时进行的操作
        # 单比特门最后一个数字表示qubit序号
        # 两比特门 ':' 前的两个数字表示对应两个control和target qubit序号，':'之后的数字 n 表示操作为 pi/n
        self.gate_re = re.compile(r'^(I|S|CP|G|X2p|X2n|Y2p|Y2n|X|Y|Z[0-9]+:)(.*)')
        self.gate_list = None
        self._N = 1
        self.initial_state = None
        self.qubit_idx = list()
        self.couple_idx = list()
    
    def get_N(self):
        self.qubit_idx = list()
        self.couple_idx = list()
        gate_re = self.gate_re
        for gate in np.hstack(np.array(self.gate_list)):
            m = gate_re.search(gate)
            if 'S' in gate or 'CP' in gate:
                if ':' in m.group(2):
                    temp = m.group(2).split(':')[0]
                    temp_idx = int(temp.split('_')[0])
                    if temp_idx not in self.qubit_idx:
                        self.qubit_idx.append(temp_idx)
                    temp_idx = int(temp.split('_')[1])
                    if temp_idx not in self.qubit_idx:
                        self.qubit_idx.append(temp_idx)
                else: 
                    temp_idx = int(m.group(2).split('_')[0])
                    if temp_idx not in self.qubit_idx:
                        self.qubit_idx.append(temp_idx)
                    temp_idx = int(m.group(2).split('_')[1])
                    if temp_idx not in self.qubit_idx:
                        self.qubit_idx.append(temp_idx)
            elif 'G' in gate:
                temp_idx = m.group(2)
                if temp_idx not in self.couple_idx:
                    self.couple_idx.append(temp_idx)
            elif 'Z' in gate:
                temp_idx = m.group(1)[1:-1]
                if temp_idx not in self.couple_idx:
                    self.couple_idx.append(temp_idx)
            else:
                temp_idx = int(m.group(2))
                if temp_idx not in self.qubit_idx:
                    self.qubit_idx.append(temp_idx)
        self.qubit_idx = np.sort(self.qubit_idx)
        if self.qubit_idx[0] > 0:
            self.qubitidx_base = self.qubit_idx[0]
        else:
            self.qubitidx_base = 0
        self._N = self.qubit_idx[-1]-self.qubit_idx[0]+1
        # 设置初始态
        if not isinstance(self.initial_state,np.ndarray) or len(self.initial_state)!=2**self._N:
            self.initial_state = np.zeros([2**self._N,1])
            self.initial_state[0][0] = 1
        return self._N
    
    def set_initial_state(self,state=None):
        self.initial_state = state
        return self.initial_state
    
    def get_U(self, gate='I0'):
        # 本征态定义为 |qN ... q2 q1 q0> 形式（如|000>,|001>,|010>...）
        # qubit_idx表示qubit序号，按照本征态定义中的N到0顺序排列
        # gate 'I', 'X2p', 'Y2p'中的一种，分别表示不操作、绕x轴转+pi/2、绕y轴转+pi/2
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
        X2p = self.get_R_x(theta = np.pi/2)
        X2n = self.get_R_x(theta = -np.pi/2)
        X = self.get_R_x(theta = np.pi)
        Y2p = self.get_R_y(theta = np.pi/2)
        Y2n = self.get_R_y(theta = -np.pi/2)
        Y = self.get_R_y(theta = np.pi)
        
        gate_re = self.gate_re
        m = gate_re.search(gate)
        if 'S' in gate:
            U = self.get_SWAP(gate)
        elif 'CP' in gate:
            U = self.get_CP(gate)
        elif 'G' in gate:
            U = np.eye(2**self._N)
        else:
            if 'Z' in gate:
                qubit_idx = int(m.group(1)[1:-1])-self.qubit_idx[0]
                U = self.get_R_z(theta = float(m.group(2))*np.pi)
            else:
                gate = m.group(1)
                qubit_idx = int(m.group(2))-self.qubit_idx[0]
                if gate=='I':
                    U = I
                elif gate=='X2p':
                    U = X2p
                elif gate=='X2n':
                    U = X2n
                elif gate=='X':
                    U = X
                elif gate=='Y2p':
                    U = Y2p
                elif gate=='Y2n':
                    U = Y2n
                elif gate=='Y':
                    U = Y
                else:
                    raise ValueError('the gate "%s" is illegal' %gate)
            for n in range(self._N-qubit_idx-1):
                U = np.kron(I, U)
            for n in range(qubit_idx):
                U = np.kron(U, I)
        return U
    
    def get_final_state(self):
        N = self.get_N()
        self.state = self.initial_state
        for gate in np.hstack(np.array(self.gate_list)):
            U = self.get_U(gate)
            self.state = np.dot(U,self.state)
        return self.state
    
    def get_final_density_metrix(self):
        state = self.get_final_state()
        self.density_matrix = np.dot(state,np.conj(state).T)
        return self.density_matrix
    
    def get_final_probability(self):
        density_matrix = self.get_final_density_metrix()
        probability = np.zeros(2**self._N)
        for idx in range(2**self._N):
            probability[idx] = np.real(density_matrix[idx][idx])
        return probability
    
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
    
    def get_R_z(self, theta):
        R_z = np.zeros([2,2])*1j
        R_z[0][0] = 1
        R_z[1][1] = np.cos(theta)+1j*np.sin(theta)
        return R_z
    
    def get_CP(self,gate):
        CP = np.eye(2**self._N)+0*1j
        control_idx,target_idx,theta = self.get_qubit_idx_and_theta(gate)
        for idx in range(2**self._N):
            m_idx_bin = bin(idx)[2:]
            if len(m_idx_bin) > control_idx and len(m_idx_bin) > target_idx:
                if m_idx_bin[control_idx]=='1' and m_idx_bin[target_idx]=='1':
                    CP[idx][idx] = np.cos(theta)+np.sin(theta)*1j
        return CP
        
    def get_SWAP(self,gate):
        SWAP = np.eye(2**self._N)+0*1j
        control_idx,target_idx,theta = self.get_qubit_idx_and_theta(gate)
        idx_list=[]
        for idx in range(2**self._N):
            m_idx_bin = bin(idx)[2:]
            for num_0 in range(int(self._N-len(m_idx_bin))):
                m_idx_bin = '0'+m_idx_bin
            if len(m_idx_bin) > control_idx and len(m_idx_bin) > target_idx:
                if theta == np.pi/1:
                    if (m_idx_bin[int(self._N-1-control_idx)]=='0' 
                        and m_idx_bin[int(self._N-1-target_idx)]=='1'):
                        SWAP[idx][idx] = 0
                        idx_list.append(idx)
                    elif (m_idx_bin[int(self._N-1-control_idx)]=='1' 
                          and m_idx_bin[int(self._N-1-target_idx)]=='0'):
                        SWAP[idx][idx] = 0
                        idx_list.append(idx)
                else:
                    if (m_idx_bin[int(self._N-1-control_idx)]=='0' 
                        and m_idx_bin[int(self._N-1-target_idx)]=='1'):
                        SWAP[idx][idx] = 1/np.sqrt(2)
                        idx_list.append(idx)
                    elif (m_idx_bin[int(self._N-1-control_idx)]=='1' 
                          and m_idx_bin[int(self._N-1-target_idx)]=='0'):
                        SWAP[idx][idx] = 1/np.sqrt(2)
                        idx_list.append(idx)
            for n in range(len(idx_list)):
                temp_idx_n = bin(idx_list[n])[2:]
                for num_0 in range(int(self._N-len(temp_idx_n))):
                    temp_idx_n = '0'+temp_idx_n
                temp_idx_n = list(temp_idx_n)
                temp_idx_n[self._N-1-control_idx] = '1'
                temp_idx_n[self._N-1-target_idx] = '1'
                temp_idx_n =''.join(temp_idx_n)
                for idx in idx_list[n+1:]:
                    temp_idx = bin(idx)[2:]
                    for num_0 in range(int(self._N-len(temp_idx))):
                        temp_idx = '0'+temp_idx
                    temp_idx = list(temp_idx)
                    temp_idx[self._N-1-control_idx] = '1'
                    temp_idx[self._N-1-target_idx] = '1'
                    temp_idx =''.join(temp_idx)
                    if temp_idx_n==temp_idx:
                        if theta == np.pi/1:
                            SWAP[idx_list[n]][idx] = 1j
                            SWAP[idx][idx_list[n]] = 1j
                        else:
                            SWAP[idx_list[n]][idx] = 1j/np.sqrt(2)
                            SWAP[idx][idx_list[n]] = 1j/np.sqrt(2)
        return SWAP
    
    def get_qubit_idx_and_theta(self,gate):
        gate_re = self.gate_re
        m = gate_re.search(gate)
        if ':' in m.group(2):
            temp = m.group(2).split(':')[0]
            theta = np.pi/float(m.group(2).split(':')[1])
            temp_idx_0 = int(temp.split('_')[0]) - self.qubit_idx[0]
            temp_idx_1 = int(temp.split('_')[1]) - self.qubit_idx[0]
        else: 
            theta = np.pi
            temp_idx_0 = int(m.group(2).split('_')[0]) - self.qubit_idx[0]
            temp_idx_1 = int(m.group(2).split('_')[1]) - self.qubit_idx[0]
        return temp_idx_0,temp_idx_1,theta
    
    def gate_list_figure(self,with_physical_op=True):
        N = self.get_N()
        length = len(np.array(self.gate_list))+2
        fig = plt.figure(figsize=[min(length,10),len(self.qubit_idx)])
        ax = fig.add_subplot(111)
        x = [i for i in range(length)]
        for idx in self.qubit_idx:
            ax.plot(x,np.zeros([length])-idx,'k-')
            ax.text(x[0]-0.5,-idx,'Q'+str(idx),fontsize=15,
                    bbox=dict(boxstyle='round,pad=0.2', fc='purple', ec='k',lw=1 ,alpha=0.5),
                    verticalalignment="center",
                    horizontalalignment="center")
        plt.xlim(x[0]-1,x[-1]+0.5)
        plt.ylim(-self.qubit_idx[-1]-0.3,-self.qubit_idx[0]+0.3)
        plt.xticks([])
        plt.yticks([])
        
        gate_re = self.gate_re
        idx = 0
        for gate in self.gate_list:
            idx = idx+1
            if isinstance(gate,list):
                for gate_child in gate:
                    self.plot_single_gate(fig=fig,ax=ax,idx=idx,gate=gate_child,with_physical_op=with_physical_op)
            else:
                self.plot_single_gate(fig=fig,ax=ax,idx=idx,gate=gate,with_physical_op=with_physical_op)
                
                
    def plot_single_gate(self,fig,ax,idx,gate,with_physical_op):
        gate_re = self.gate_re
        m = gate_re.search(gate)
        gate_name = m.group(1)
        if ':' in m.group(2):
            theta_idx = m.group(2).split(':')[1]
        else:
            theta_idx = 1
        if 'S' in gate or 'CP' in gate:
            control_idx,target_idx,theta = self.get_qubit_idx_and_theta(gate)
            if 'S' in gate:
                ax.plot([idx,idx],[-control_idx-self.qubit_idx[0],-target_idx-self.qubit_idx[0]],'k-')
                if with_physical_op:
                    ax.plot(idx,-control_idx-self.qubit_idx[0],'rX',markersize ='10')
                    ax.plot(idx,-target_idx-self.qubit_idx[0],'bX',markersize ='10')
                else:
                    ax.plot(idx,-control_idx-self.qubit_idx[0],'kX',markersize ='10')
                    ax.plot(idx,-target_idx-self.qubit_idx[0],'kX',markersize ='10')
            else:
                ax.plot(idx,-control_idx-self.qubit_idx[0],'k.',markersize ='15')
                ax.plot(idx,-target_idx-self.qubit_idx[0],'k.',markersize ='15')
                ax.text(idx,-target_idx-self.qubit_idx[0],'$\pi$/'+str(theta_idx),fontsize=10,
                        bbox=dict(boxstyle='round,pad=0.2', fc='lightgrey', ec='k',lw=1 ,alpha=1.0),
                        verticalalignment="center",
                        horizontalalignment="center")
                ax.plot([idx,idx],[-control_idx-self.qubit_idx[0],-target_idx-self.qubit_idx[0]],'k-')
        elif 'G' in gate:
            if with_physical_op:
                couple_idx0 = int(m.group(2).split('_')[0])
                couple_idx1 = int(m.group(2).split('_')[1])
                #ax.plot([idx,idx],[-couple_idx0,-couple_idx1],'k--')
                ax.text(idx,-(couple_idx0+couple_idx1)/2,'G',fontsize=15,
                        bbox=dict(boxstyle='round,pad=0.2', fc='lightskyblue', ec='k',lw=1 ,alpha=1.0),
                        verticalalignment="center",
                        horizontalalignment="center")
        elif 'Z' in gate:
            qubit_idx = int(m.group(1)[1:-1])
            ax.text(idx,-qubit_idx,'Z'+'$_{%.2f\pi}$'%(float(m.group(2))),fontsize=10,
                    bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='k',lw=1 ,alpha=1.0),
                    verticalalignment="center",
                    horizontalalignment="center")
        else:
            qubit_idx = int(m.group(2))
            ax.text(idx,-qubit_idx,gate_name,fontsize=10,
                    bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='k',lw=1 ,alpha=1.0),
                    verticalalignment="center",
                    horizontalalignment="center")
                