import os
import datetime
import numpy as np


def save(path=None, name=None, x=None, y=None, z=None):
    if not path:
        time_list = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        time_list = time_list.split('-')
        path = os.path.join('tempdata',time_list[0]+time_list[1]+time_list[2])
    if not os.path.exists(path):
        os.makedirs(path)
    file_path = os.path.join(path,name+'.npz')
    print(file_path)
    if x.any() and y.any() and z.any():
        np.savez(file_path,x=x,y=y,z=z)
    elif x.any() and y.any():
        np.savez(file_path,x=x,y=y)
    elif x.any():
        np.savez(file_path,x=x)
    else:
        raise 'the data format to be saved is illegal'