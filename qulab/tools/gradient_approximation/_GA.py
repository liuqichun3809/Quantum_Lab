import numpy as np

class gradient_approximation(object):
    ## 当有多个自变量时，尽量将自变量“归一化”
    ## 即在某一个点上，目标函数值在各自变量方向上的梯度尽量接近
    ## 若各方向上的梯度相差很大，容易出现各方向收敛速度差别较大的情况
    ## 出现振荡不收敛情况时，可适当减小梯度系数（self.gradient_ratio_init）的值
    ## 在使用该类时，注意需要对“get_function_result”函数重新定义
    def __init__(self):
        self.alpha = 0.1
        self.gama = 0.1
        self.gradient_ratio_init = 0.5
        self.variable_ratio_init = 0.5
        self.step_num = 20
        self.variable_init = np.array([0,0])#单个参数时也需要写成array格式
        self.variable_delta = np.array([0.99,0.99])#单个参数时也需要写成array格式
        self.variable_list = []
        self.function_result_list = []
        
    def get_function_result(self,variable,**key):
        # 注意 variable 是array格式的
        # 该函数只是示例，需要根据具体要进行的测试编写
        return (variable[0]+1)**2+(variable[1]-0.5)**2+np.random.rand()*0.01
    
    """
    ## 例如以下是对H2分子的VQE模拟
    from qulab.tools.gate_sequence_simulator._GSS import *
    def get_function_result(self,variable,**key):
        g = key['g']
        simulator = GSS()
        gate_list = ['X0',['X2n0','Y2p1'],'Y2n0','CP1_0','Y2p0','Z0:0.0','Y2n0','CP1_0','Y2p0',['X2p0','Y2n1'],['I0','I1']]
        gate_list[5] = 'Z0:'+str(variable[0])
        gate_list[-1] = ['I0','I1']
        simulator.gate_list = gate_list
        pro = simulator.get_final_probability()
        Z0I1_pro = pro[0]-pro[1]+pro[2]-pro[3]
        I0Z1_pro = pro[0]+pro[1]-pro[2]-pro[3]
        Z0Z1_pro = pro[0]-pro[1]-pro[2]+pro[3]

        gate_list[-1] = ['X2n0','X2n1']
        simulator.gate_list = gate_list
        pro = simulator.get_final_probability()
        Y0Y1_pro = pro[0]-pro[1]-pro[2]+pro[3]

        gate_list[-1] = ['Y2n0','Y2n1']
        simulator.gate_list = gate_list
        pro = simulator.get_final_probability()
        X0X1_pro = pro[0]-pro[1]-pro[2]+pro[3]
        pro_array = np.array([Z0I1_pro,I0Z1_pro,Z0Z1_pro,Y0Y1_pro,X0X1_pro]).T
        energy = np.dot(g[1:],pro_array)+g[0]
        return energy+np.random.rand()*0.005
    """
    
    def do_approximation(self,**key):
        self.variable_list = []
        self.variable_list.append(self.variable_init)
        self.function_result_list = []
        for step in range(self.step_num):
            gradient = np.zeros(len(self.variable_list[step]))
            if step == 0:
                temp_f_delta = 0
                for idx in range(len(self.variable_list[step])):
                    variable_delta = np.zeros(len(self.variable_list[step]))
                    # 根据初始参数附近的结果计算梯度
                    variable_delta[idx] = self.variable_ratio_init*self.variable_delta[idx]
                    variable_p = self.variable_list[step]+variable_delta
                    variable_n = self.variable_list[step]-variable_delta
                    f_p = self.get_function_result(variable = variable_p, **key)
                    f_n = self.get_function_result(variable = variable_n, **key)
                    temp_f_delta = temp_f_delta+f_p-f_n
                    self.variable_ratio = self.variable_ratio_init
                    # 计算梯度
                    gradient[idx] = (f_p-f_n)*self.variable_delta[idx]**(step+1)/(2*self.variable_ratio)
                # 更新梯度系数和变量的变化系数
                self.gradient_ratio_init = self.gradient_ratio_init*self.variable_ratio_init/abs(temp_f_delta/len(self.variable_list[step]))
                self.gradient_ratio = self.gradient_ratio_init
            else:
                # 更新梯度系数和变量的变化系数
                self.gradient_ratio = self.gradient_ratio_init/(step**self.alpha)
                self.variable_ratio = self.variable_ratio_init/(step**self.gama)
                for idx in range(len(self.variable_list[step])):
                    variable_delta = np.zeros(len(self.variable_list[step]))
                    # 获取当前变量附近的结果
                    variable_delta[idx] = self.variable_ratio_init*self.variable_delta[idx]
                    variable_p = self.variable_list[step]+variable_delta
                    variable_n = self.variable_list[step]-variable_delta
                    f_p = self.get_function_result(variable = variable_p, **key)
                    f_n = self.get_function_result(variable = variable_n, **key)
                    # 计算梯度
                    gradient[idx] = (f_p-f_n)*self.variable_delta[idx]**((step+1)/2)/(2*self.variable_ratio)
            # 获取更新后的变量对应的结果
            self.variable_list.append(self.variable_list[step]-self.gradient_ratio*gradient)
            self.function_result_list.append(self.get_function_result(variable = self.variable_list[step+1], **key))