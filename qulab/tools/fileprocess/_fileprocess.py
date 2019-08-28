import os
import datetime
import numpy as np
import matplotlib.pyplot as plt
from qulab._app import getAppClass


## 将数据或者record存储为npz文件
def save(path=None, name=None, x=None, y=None, z=None, tag=' ', record=None):
    if not path:
        time_list = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        time_list = time_list.split('-')
        path = os.path.join('tempdata',time_list[0]+time_list[1]+time_list[2])
    if not os.path.exists(path):
        os.makedirs(path)
    if '.npz' in name:
        file_path = os.path.join(path, name)
    else:
        file_path = os.path.join(path,name+'.npz')
    print(file_path)
    if record is None:
        if x.any() and y.any() and z.any():
            np.savez(file_path,x=x,y=y,z=z,tag=tag)
        elif x.any() and y.any():
            np.savez(file_path,x=x,y=y,tag=tag)
        elif x.any():
            np.savez(file_path,x=x,tag=tag)
        else:
            assert True,'the data format to be saved is illegal'
    else:
        info = get_record_info(record)
        for item in info:
            tag = tag+'\n'+item+': '+str(info[item])
        data = record.data
        if len(data)==3:
            np.savez(file_path,x=data[0],y=data[1],z=data[2],tag=tag)
        elif len(data)==2:
            np.savez(file_path,x=data[0],y=data[1],tag=tag)
        elif len(data)==1:
            np.savez(file_path,x=data,tag=tag)
        else:
            assert True,'the data format to be saved is illegal'


## 获取record的信息
def get_record_info(Record):
    information = {'created time': str(Record.created_time),
                   'finished time': str(Record.finished_time),
                   'title': str(Record.title),
                   'tags': str(Record.tags),
                   'parameters': str(Record.params)}
    return information


## 将npz文件转存为txt文件
def npz2txt(npz_path='',txt_path=''):
    ## 确认输出txt文件的路径和文件名
    if not txt_path:
        assert txt_path,'No output txt file path, please check it!'
    elif '.txt' in txt_path:
        (file_dir, file) = os.path.split(txt_path)
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
    else:
        if not os.path.exists(txt_path):
            os.makedirs(txt_path)
        (file_dir, file) = os.path.split(npz_path)
        (file_name, extension) = os.path.splitext(file)
        txt_path = os.path.join(txt_path,file_name+'.txt')
    
    ## 将数据写入txt文件
    fid = open(txt_path,'w+')
    data = np.load(npz_path)
    for item in data:
        fid.write('\n'+item+' data:\n')
        if item=='x' or item=='y':
            for temp_data in data[item]:
                fid.write(str(temp_data)+'\n')
        elif item=='z':
            row, col = data[item].shape
            for idx_row in range(row):
                for idx_col in range(col):
                    fid.write(str(data[item][idx_row][idx_col])+'   ')
                fid.write('\n')
        else:
            fid.write(str(data[item]))
    fid.close()


## 将record存储为txt文件
def record2txt(record=None, txt_path='', tag=' ', png=True):
    ## 确认输出txt文件的路径和文件名
    if not txt_path:
        assert txt_path,'No output txt file path, please check it!'
    elif '.txt' in txt_path:
        (file_dir, file) = os.path.split(txt_path)
        (file_name, extension) = os.path.splitext(file)
        jpg_path = os.path.join(file_dir,file_name+'.png')
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
    else:
        if not os.path.exists(txt_path):
            os.makedirs(txt_path)
        jpg_path = os.path.join(txt_path,str(record.title)+'.png')
        txt_path = os.path.join(txt_path,str(record.title)+'.txt')
    
    ## 存储数据
    info = get_record_info(record)
    for item in info:
        tag = tag+'\n'+item+': '+str(info[item])
    data = record.data
    xyz = ['x','y','z']
    
    fid = open(txt_path,'w+')
    fid.write('tag: \n')
    fid.write(tag+'\n')
    
    for idx in range(len(data)):
        fid.write('\n'+xyz[idx]+' data:\n')
        if xyz[idx]=='x' or xyz[idx]=='y':
            for temp_data in data[idx]:
                fid.write(str(temp_data)+'\n')
        else:
            row, col = data[idx].shape
            for idx_row in range(row):
                for idx_col in range(col):
                    fid.write(str(data[idx][idx_row][idx_col])+'   ')
                fid.write('\n')
    fid.close()
    
    ## 将数据对应的图存储为相同文件名的jpg，以便查看
    if png:
        title = info['title']
        title = title.split(' ')
        fullname = title[2].split('.')
        version = title[3][2:-1]
        
        app=getAppClass(name=fullname[1],
                        package=fullname[0],
                        version=version)
        fig = plt.figure()
        app.plot(fig,record.data)
        plt.savefig(jpg_path)