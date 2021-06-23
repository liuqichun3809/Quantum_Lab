import os
import datetime
import re
import pymongo
import numpy as np
import matplotlib.pyplot as plt
from qulab._app import getAppClass
import qulab


## 将数据或者record存储为npz文件
def save(path=None, name=None, x=None, y=None, z=None, tag=' ', record=None, source_type=False):
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
    #print(file_path)
    if record is None:
        if source_type:
            np.savez(file_path,x=x,tag=tag)
        else:
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
        if source_type:
            np.savez(file_path,x=data,tag=tag)
        else:
            if len(data)==3:
                np.savez(file_path,x=data[0],y=data[1],z=data[2],tag=tag)
            elif len(data)==2:
                np.savez(file_path,x=data[0],y=data[1],tag=tag)
            elif len(data)==1:
                np.savez(file_path,x=data,tag=tag)
            else:
                np.savez(file_path,data=[data,tag],tag=tag)
                #assert True,'the data format to be saved is illegal'


## 获取record的信息
def get_record_info(Record):
    information = {'created time': str(Record.created_time),
                   'finished time': str(Record.finished_time),
                   'title': str(Record.title),
                   'tags': str(Record.tags),
                   'parameters': str(Record.params),
                   'settings':str(Record.settings)}
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
    data = np.load(npz_path,allow_pickle=True)
    for item in data:
        fid.write('\n'+item+' data:\n')
        if item=='x' or item=='y':
            for temp_data in data[item]:
                fid.write(str(temp_data)+'\n')
        #elif item=='z':
        #    shape = data[item].shape
        #    row = shape[0]
        #    col = shape[1]
        #    for idx_row in range(row):
        #        for idx_col in range(col):
        #            fid.write(str(data[item][idx_row][idx_col])+'   ')
        #        fid.write('\n')
        else:
            fid.write(str(data[item]))
    fid.close()


## 将record存储为txt文件
def record2txt(record=None, txt_path='', tag=' ', png=True, fig_title=None):
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
    
    try:
        # 当record数据为data=[x,y,z]格式时
        if len(np.array(data[len(data)-1]).shape)==2 and len(data)>2:
            fid.write('\n'+'data text format:\n')
            fid.write('000000      y axis\n')
            fid.write('x axis      z data\n')
            if len(data)>3:
                fid.write('!!! This data has more than two parts, for example, PNA outputs have amp and phase. !!!\n')
            fid.write('\n'+'data begin:\n')
            for idx_z in range(len(data)-2):
                fid.write('000000     ')
                for y in data[1]:
                    fid.write(str(y)+'     ')
                fid.write('\n')
                for idx_col in range(len(data[0])):
                    fid.write(str(data[0][idx_col])+'     ')
                    for idx_row in range(len(data[1])):
                        fid.write(str(data[idx_z+2][idx_row][idx_col])+'     ')
                    fid.write('\n')
                fid.write('\n\n')
            """
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
            """
        # 当record数据为data=[x,y,y,...]格式时
        else:
            for idx in range(len(data)):
                    if idx==0:
                        fid.write('\n'+'x data:    ')
                    else:
                        fid.write('y data:    ')
            fid.write('\n'+'data begin:\n')
            for n in range(len(data[0])):
                for idx in range(len(data)):
                    if isinstance(data[idx], np.ndarray):
                        fid.write(str(data[idx][n])+'    ')
                    else:
                        fid.write(str(data[idx])+'    ')
                fid.write('\n')
    except IndexError:
        fid.write('\n'+'\n'+'\n'+'correct data begin:\n')
        for idx in range(len(data)):
            fid.write(str(data[idx])+'\n')
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
        if fig_title is None:
            fig = plt.figure()
        else:
            fig = plt.figure(fig_title)
        app.plot(fig,record.data)
        plt.savefig(jpg_path)

        
## 将record存储为npz和txt文件
def record_to_npz_and_txt(path=None, name=None, tag=' ', record=None, png=True, fig_title=None):
    info = get_record_info(record)
    save(path=path, name=name, tag=tag, record=record)
    npz2txt(npz_path=os.path.join(path,name)+'.npz',txt_path=os.path.join(path,name)+'.txt')
    ## 将数据对应的图存储为相同文件名的jpg，以便查看
    if png:
        title = info['title']
        title = title.split(' ')
        fullname = title[2].split('.')
        version = title[3][2:-1]
        
        app=getAppClass(name=fullname[1],
                        package=fullname[0],
                        version=version)
        if fig_title is None:
            fig = plt.figure()
        else:
            fig = plt.figure(fig_title)
        app.plot(fig,record.data)
        plt.savefig(os.path.join(path,name)+'.png')


## 根据输入app的fullname和record的index，删除record数据
def del_record(database='qulab',fullname='package.app',index=[]):
    ## 注意删除record后，用display()看到的index会更新
    ## 参数格式fullname='package.app',index=[*,*,*]
    ## 若index=['all']，则删除fullname对应的所有record
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    mydb = myclient[database]
    mycol = mydb["record"]
    
    # 由于每删除一条record数据，qulab.query()获取的recordset的index就会变化，
    # 所以先用record_list将要删除的所有record信息（created_time）记录下来，再根据created_time删除数据
    if index[0]=='all':
        index = [i for i in range(qulab.query(fullname).count())]
    record_list = {}
    for idx in index:
        created_time = get_record_info(qulab.query(fullname)[idx])['created time']
        record_list[str(idx)] = re.sub(r'\D',',',created_time)
    for item in record_list:
        myquery = {'created_time': record_list[item]}
        mycol.delete_one(myquery)
