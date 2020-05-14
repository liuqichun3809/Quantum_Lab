import os
import platform
import numpy as np
import scipy.io as sio
import matlab.engine

matlab_eng = matlab.engine.start_matlab()
if platform.system() in ['Darwin', 'Linux']:
    home = os.getenv('HOME')
elif platform.system() == 'Windows':
    home = os.getenv('ProgramData')
else:
    home = os.getcwd()
mat_file_dir = os.path.join(home,'Quantum_Lab')


class MLE(object):
    def __init__(self):
        self.meas_data = None
        self.density = None
        self.max_evals = 1500
        self.matlab_file_dir = r'E:\2.code\Quantum_Lab\qulab\tools\QST_by_MLE'
        
    def save_meas_data_to_mat(self):
        meas_data_mat_path = os.path.join(mat_file_dir,'meas_data.mat')
        sio.savemat(meas_data_mat_path,{'meas_data': self.meas_data,'max_evals': self.max_evals})
        return self.meas_data
        
    def do_MLE(self):
        matlab_eng.cd(self.matlab_file_dir)
        meas_data = self.save_meas_data_to_mat()
        matlab_eng.N_qubit_qst(nargout=0)
        
    def get_density_mstrix(self):
        result_data_path = os.path.join(mat_file_dir,'MLE_result.mat')
        result = sio.loadmat(result_data_path)
        return result['rho']