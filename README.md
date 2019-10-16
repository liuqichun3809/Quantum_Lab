# Quantum_Lab
[https://github.com/liuqichun3809/Quantum_Lab]

Quantum_Lab 继承于 QuLab[https://github.com/feihoo87/QuLab/]

## 功能：以Python语言实现对各种实验设备的控制，进行实验测试和数据采集，运行方式为jupyter notebook。

## 软件信息：
    1. 顶层为qulab项目和setup信息。
    2. qulab包含：设备驱动配置模块drivers和device、用户工具模块tools、软件管理模块。
    3. 软件的代码、数据存储管理、仪器配置、用户信息等通过MongoDB实现。


## 软件安装准备工作
    1. Python安装：
        从官网(https://www.python.org/) 下载安装，选择3.6以上版本，默认自带pip包管理工具，
        安装完成后在命令窗口以‘pip --version’查看是否有pip包管理工具，
        若无该管理工具，则可通过官网(https://pypi.org/project/pip/) 进行安装。
    2. MongoDB安装：
        从官网(https://www.mongodb.com/download-center/community) 选择对应操作系统的版本进行下载安装，
        安装和配置过程请参考https://www.runoob.com/mongodb/mongodb-tutorial.html 教程。
    3. Jupyter安装：
        命令窗口中pip指令‘pip install jupyter’
    4. Python工具包安装：
        在程序运行中若缺失某种工具包，则在命令窗口通过‘pip install ***’进行安装，
        由于一些工具包默认从境外的网站下载安装，速度较慢，可以采用镜像源，
        安装命令为‘pip install -i https://pypi.tuna.tsinghua.edu.cn/simple ***’，
        其中‘***’为需要安装的工具包名称。
        windows系统下，用pip安装工具包出现“microsoft visual c++ 14.0 is required"错误时，
        可以手动去”https://www.lfd.uci.edu/~gohlke/pythonlibs/#wordcloud" 下载要安装的工具包到本地，
        然后在pip安装下载好的本地工具包
    5. git工具安装：
        若系统未安装git，则可以按照“https://www.git-scm.com/book/en/v2/Getting-Started-Install-Git" 的说明,
        选择对应系统进行安装。
    6. Quantum_Lab安装：
        1）$ cd /*/*/*（其中‘/*/*/*’为准备安装Quantum_Lab的路径）
        2）$ git clone https://github.com/liuqichun3809/Quantum_Lab.git
        3）$ cd Quantum_Lab
        4）$ pip install .
        若对Quantum_Lab内的代码进行了修改，则需要从新执行第3）和4）步，修改才能生效。
    7. 制作 ssl 证书，用于 InstrumentServer 加密，参考'create_config_yaml.md'文件。
    8. 创建配置文件 `config.yaml`，若使用 Windows 系统，将其置于`%ProgramData%\QuLab\`路径下，
       参考'create_config_yaml.md'文件。


## 软件运行前MongoDB启动准备
    1. $ cd /usr/local/mongodb/bin（若不是该路径，则改为对应mongodb安装的路径）
    2. $ sudo ./mongod
       此操作为开启MongoDB的服务端口，若未开启该服务端口，则Quantum_Lab程序无法进行代码和数据管理，从而无法使用。
       若要通过命令窗口查看MongoDB数据库，则进入到/usr/local/mongodb/bin，然后执行‘mongo’指令。
    3. 也可以将路劲添加到系统环境变量path里，然后在任意路劲下直接运行 $ mongod即可。


## 使用

### 创建初始用户

```python
from qulab.admin import register
register()
```

### 登陆系统

```python
import qulab
qulab.login()
```

### 创建并运行简单 App

定义 App

```python
import numpy as np
import asyncio
import qulab

class TestApp(qulab.Application):
    '''一个简单的 App'''
    async def work(self):
        async for x in self.sweep['x']:
            yield x, np.random.randn()

    async def set_x(self, x):
        await asyncio.sleep(0.5)
        # print('x =', x)

    @staticmethod
    def plot(fig, data):
        x, y = data
        ax = fig.add_subplot(111)
        ax.plot(x, y)
        ax.set_xlabel('x (a.u.)')
        ax.set_ylabel('y (a.u.)')
```
将其提交到数据库
```python
TestApp.save(package='test')
```
一旦将App提交到数据库，以后就不必重复将代码复制过来运行了。直接配置并运行即可。
```python
import qulab
import numpy as np

app = lab.make_app('TestApp', package='test').sweep([
    ('x', np.linspace(0, 1, 11))
])
qulab.make_figure_for_app(app)
app.run()
```

### 创建复杂一点的 App

```python
import numpy as np
import asyncio
import qulab

class ComplexApp(lab.Application):
    '''一个复杂点的 App'''
    async def work(self):
        async for y in self.sweep['y']:
            # 一定要注意设置 parent
            app = qulab.make_app('test.TestApp', parent=self)
            x, z = await app.done()
            yield x, y, z

    async def set_y(self, y):
        await asyncio.sleep(0.5)
        # print('x =', x)

    def pre_save(self, x, y, z):
        if self.data.rows > 1:
            x = x[0]
        return x, y, z

    @staticmethod
    def plot(fig, data):
        x, y, z = data
        ax = fig.add_subplot(111)
        if isinstance(y, np.ndarray):
            ax.imshow(z, extent=(min(x), max(x), min(y), max(y)),
                     aspect='auto', origin='lower', interpolation='nearest')
        else:
            ax.plot(x, z)
        ax.set_xlabel('x (a.u.)')
        ax.set_ylabel('y (a.u.)')
```
保存
```python
ComplexApp.save(package='test')
```
运行

```python
import qulab
import numpy as np

app = qulab.make_app('ComplexApp', package='test').sweep([
    ('x', np.linspace(0, 1, 11)),
    ('y', np.linspace(3,5,11))
])
qulab.make_figure_for_app(app)
qulab.make_figures_for_App('TestApp')
app.run()
```

### 涉及到仪器操作

1. 安装 drivers
```python
import os

path = 'path/to/drivers'

for f in os.listdir(path):
    qulab.admin.uploadDriver(os.path.join(path, f))
```

2. 查看已有的 drivers
```python
qulab.listDrivers()
```

3. 添加仪器设置
```python
# 第一台网分
qulab.admin.setInstrument('PNA-I', 'localhost', 'TCPIP::10.122.7.250', 'NetworkAnalyzer')
# 第二台网分
qulab.admin.setInstrument('PNA-II', 'localhost', 'TCPIP::10.122.7.251', 'NetworkAnalyzer')
```

4. 查看已存在的仪器

```python
qulab.listInstruments()
```
5. 连接仪器
```python
pna=qulab.open_resource('PNA-I')
```

6. 定义 App
```python
import numpy as np
import skrf as rf
from qulab import Application


class S21(Application):
    '''从网分上读取 S21

    require:
        rc : PNA
        settings: repeat(optional)

    return: Frequency, Re(S21), Im(S21)
    '''
    async def work(self):
        if self.params.get('power', None) is None:
            self.params['power'] = [self.rc['PNA'].getValue('Power'), 'dBm']
        x = self.rc['PNA'].get_Frequency()
        for i in range(self.settings.get('repeat', 1)):
            self.processToChange(100.0 / self.settings.get('repeat', 1))
            y = np.array(self.rc['PNA'].get_S())
            yield x, np.real(y), np.imag(y)
            self.increaseProcess()

    def pre_save(self, x, re, im):
        if self.data.rows > 1:
            x = x[0]
            re = np.mean(re, axis=0)
            im = np.mean(im, axis=0)
        return x, re, im

    @staticmethod
    def plot(fig, data):
        x, re, im = data
        s = re + 1j * im
        ax = fig.add_subplot(111)
        ax.plot(x / 1e9, rf.mag_2_db(np.abs(s)))
        ax.set_xlabel('Frequency / GHz')
        ax.set_ylabel('S21 / dB')
```
7. 保存
```python
S21.save(package='PNA')
```
8. 运行
```python
import qulab

app = lab.make_app('PNA.S21').with_rc({
    'PNA': 'PNA-II'     # PNA-II 必须是已经添加到数据库里的设备名
}).with_settings({
    'repeat': 10
}).with_params(
    power = [-27, 'dBm'],
    att = [-30, 'dB']
).with_tags('5 bits sample', 'Cavity 1')

qulab.make_figure_for_app(app)

app.run()
```

### 查询

1. 查看已有的 App
```python
qulab.listApps()
```

2. 查询数据
```python
results = qulab.query('PAN.S21')
results.display()
```

3. 获取原始数据

```python
res = qulab.query(app='TestApp')
x,y = res[0].data

import matplotlib.pyplot as plt
plt.plot(x, y)
plt.show()
```

## License

[MIT](https://opensource.org/licenses/MIT)
