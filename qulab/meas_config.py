import datetime
from pathlib import Path
from ruamel import yaml


class config_info():
    """
    加载meas_config文件，返回测试相关信息
    """ 
    def __init__(self, **kw):
        self.config_path = r'E:\qubit_measurent_20200108\auto_meas_app\config_info.yaml'
    
    def load_config(self):
        path = Path(self.config_path)
        return yaml.safe_load(path.read_text())
    
    def update_config(self, config=None):
        time_list = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        config['updata_time'] = time_list
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, Dumper=yaml.RoundTripDumper)
        return 'ok'
    
    def update_carry(self):
        config = self.load_config()
        meas_freq = config['meas_info']['mw_freq']
        drive_freq = config['drive_info']['mw_freq']
        keys = list(config['qubit_info'].keys())
        for key in keys:
            config['meas_info']['carry'][key] = float(config['qubit_info'][key]['probe_freq'])-float(meas_freq)
            config['drive_info']['carry'][key] = float(config['qubit_info'][key]['f01'])-float(drive_freq)
        self.update_config(config=config)
        return 'ok'