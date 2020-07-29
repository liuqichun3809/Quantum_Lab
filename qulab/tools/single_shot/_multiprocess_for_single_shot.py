import datetime
import numpy as np
import multiprocessing as mp
from qulab.tools.wavedata import *

def MP_func(I_data, Q_data, IF_filter0, IF_filter1, IF, sRate):
    qubit_I0 = []
    qubit_Q0 = []
    for idx in range(int((I_data.shape)[0])):
        I = I_data[idx]
        Q = Q_data[idx]
        wd_raw = Wavedata(I+1j*Q,sRate=sRate).filter(IF_filter0)
        wd_raw = wd_raw.filter(IF_filter1)
        iqcali = A.Analyze_cali(wd_raw, IF)
        wd_f = A.Homodyne(wd_raw, freq=IF, cali=iqcali)
        amp_I = np.mean(Wavedata.I(wd_f).data[50:-50])
        amp_Q = np.mean(Wavedata.Q(wd_f).data[50:-50])
        qubit_I0.append(amp_I)
        qubit_Q0.append(amp_Q)
    return np.array([np.array(qubit_I0),np.array(qubit_Q0)])

def get_IQ(chA, chB, IF_filter0, IF_filter1, IF, sRate):
    num_cores = int(mp.cpu_count())
    record_per_processor = int((chA.shape)[0]/num_cores)
    param_dict=[]
    for n in range(num_cores-1):
        I_data = chA[int(n*record_per_processor):int((n+1)*record_per_processor)]
        Q_data = chB[int(n*record_per_processor):int((n+1)*record_per_processor)]
        param_dict.append((I_data, Q_data, IF_filter0, IF_filter1, IF, 1e9))
    I_data = chA[int((num_cores-1)*record_per_processor):]
    Q_data = chB[int((num_cores-1)*record_per_processor):]
    param_dict.append((I_data, Q_data, IF_filter0, IF_filter1, IF, 1e9))
    
    pool = mp.Pool(num_cores)
    results = [pool.apply_async(MP_func, args=(I_data, Q_data, IF_filter0, IF_filter1, IF, sRate)) 
               for I_data, Q_data, IF_filter0, IF_filter1, IF, sRate in param_dict]
    results = [p.get() for p in results]
    pool.close()
    pool.join()
    results = np.hstack(results)
    return results