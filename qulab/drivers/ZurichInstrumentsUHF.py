# -*- coding: utf-8 -*-
import zhinst
import zhinst.utils

import numpy as np
import textwrap
import time
import os

from qulab.device import BaseDriver, QInteger, QOption, QReal, QString, QVector

# define API version
ZI_API = 6


class Driver(BaseDriver):
    support_models = ['UHFAWG',]
    quants = [
        QOption('SampleRate', ch=0, get_cmd='/awgs/0/time',
                options = [
                    ('1.8G', 0),
                    ('900M', 1),
                    ('450M', 2),
                    ('225M', 3),
                    ('112.5M', 4),
                    ('56.25M', 5),
                    ('28.12M', 6)]),
        QOption('Output', ch=0, get_cmd='/sigouts/%(ch)d/on',
                options = [
                    ('ON', 1),
                    ('OFF', 0)]),
        QOption('Imp50', ch=0, get_cmd='/sigouts/%(ch)d/imp50',
                options = [
                    ('ON', 1),
                    ('OFF', 0)]),
        QOption('MaxRange', ch=0, get_cmd='/sigouts/%(ch)d/range',
                options = [
                    ('0.075', 0.075),
                    ('0.75', 0.75)]),
        QReal('Offset', value=0, unit='V', ch=0, get_cmd='/sigouts/%(ch)d/offset'),
        QReal('Amplitude', value=1.0, unit='1', ch=0, get_cmd='/awgs/0/outputs/%(ch)d/amplitude'),
        QOption('RunMode', get_cmd='/awgs/0/single',
                options = [
                    ('Continuous', 1),
                    ('Triggered', 0)]),
        QOption('TrigChannel', get_cmd='/awgs/0/auxtriggers/0/channel',
                options = [
                    ('TrigIn1', 0),
                    ('TrigIn2', 1),
                    ('TrigIn3', 2),
                    ('TrigIn4', 3)]),
        QOption('TrigSlope', get_cmd='/awgs/0/auxtriggers/0/slope',
                options = [
                    ('Level', 0),
                    ('Rise', 1),
                    ('Fall', 2),
                    ('Both', 3)]),
        # AWG modulation，Plain means no，Modulation means yes，
        # ch=0, ch=1 can only be modulated by the following Sig~3、Sig~7，
        QOption('Modulation', ch=0, get_cmd='/awgs/0/outputs/%(ch)d/mode',
                options = [
                    ('Plain', 0),
                    ('Modulation', 1)]),
        
        # set oscillator freq，max is 600e6Hz, 'ch' is oscillator index, should be within（0~7）
        QReal('OscFreq', value=10e6, unit='Hz', ch=0, get_cmd='/oscs/%(ch)d/freq'),
        # set the corresponding oscillator of every inter signal, 'ch' is Sig index（0~7），'value' is oscillator index（0~7）
        QReal('SigOsc', value=0, ch=0, get_cmd='/demods/%(ch)d/oscselect'),
        
        # set the amp of inter signal(index=0), and it will be add to output channel 'ch', unit='V'，limitted by ’MaxRange‘
        QReal('Sig0Amp', value=0., unit='V', ch=0, get_cmd='/sigouts/%(ch)d/amplitudes/0'),
        # set the amp of inter signal(index=1), and it will be add to output channel 'ch', unit='V'，limitted by ’MaxRange‘
        QReal('Sig1Amp', value=0., unit='V', ch=0, get_cmd='/sigouts/%(ch)d/amplitudes/1'),
        
        # enable adding signal(index=0) to output channel 'ch'
        QOption('Sig0Enable', ch=0, get_cmd='/sigouts/%(ch)d/enables/0',
                options = [
                    ('enable', 1),
                    ('disable', 0)]),
        # enable adding signal(index=1) to output channel 'ch'
        QOption('Sig1Enable', ch=0, get_cmd='/sigouts/%(ch)d/enables/1',
                options = [
                    ('enable', 1),
                    ('disable', 0)]),
        
        # set signal input info, ch means signal index（0、1）
        QOption('Sig_In_Channel', ch=0, get_cmd='/scopes/0/channels/%(ch)d/inputselect',
                options = [
                    ('signalinput1', 0),
                    ('signalinput2', 1),
                    ('trigger1', 2),
                    ('trigger2', 3)]),
        QOption('Sig_In_SampleRate', ch=0, get_cmd='/scopes/0/time',
                options = [
                    ('1.8G', 0),
                    ('900M', 1),
                    ('450M', 2),
                    ('225M', 3),
                    ('112M', 4),
                    ('56M', 5),
                    ('28M', 6),
                    ('14M', 7)]),
        QOption('Sig_In_RunMode', get_cmd='/scopes/0/single',
                options = [
                    ('Continuous', 1),
                    ('Triggered', 0)]),
        QOption('Sig_In_TrigChannel', get_cmd='/scopes/0/trigchannel',
                options = [
                    ('TrigIn1', 0),
                    ('TrigIn2', 3)]),
        QOption('Sig_In_TrigEnable', get_cmd='/scopes/0/trigenable',
                options = [
                    ('enable', 1),
                    ('disable', 0)]),
        QReal('Record_length', value=1000, unit='point', ch=0, get_cmd='/scopes/0/length'),
        QOption('Sig_In_Imp50', ch=0, get_cmd='/sigins/%(ch)d/imp50',
                options = [
                    ('ON', 1),
                    ('OFF', 0)]),
        QOption('Sig_In_AC', ch=0, get_cmd='/sigins/%(ch)d/ac',
                options = [
                    ('ON', 1),
                    ('OFF', 0)]),
        QReal('Sig_In_Range', value=1.0, unit='V', ch=0, get_cmd='/sigins/%(ch)d/range'),
        QOption('Sig_In_Diffmode', ch=0, get_cmd='/sigins/%(ch)d/diff', 
                options = [('OFF', 0), 
                           ('Sig1-Sig2', 2), 
                           ('Sig2-Sig1', 3)]),
        QOption('Sig_In_TrigSlope', get_cmd='/scopes/0/trigslope',
                options = [
                    ('Level', 0),
                    ('Rise', 1),
                    ('Fall', 2),
                    ('Both', 3)]),
        QReal('Sig_In_TrigLevel', value=0.5, unit='V', ch=0, get_cmd='/scopes/0/triglevel'),
        QReal('Sig_In_TrigDelay', value=100e-9, unit='s', ch=0, get_cmd='/scopes/0/trigdelay'),
        
        # set aux channel
        QOption('Aux_output_select', ch=0, get_cmd='/auxouts/%(ch)d/outputselect',
                options = [
                    ('AWG', 4),
                    ('Manual', -1)]),
        QOption('Aux_demod_select', ch=0, get_cmd='/auxouts/%(ch)d/demodselect',
                options = [
                    ('aux_ch0', 0),
                    ('aux_ch1', 1),
                    ('aux_ch2', 2),
                    ('aux_ch3', 3)]),
        QReal('Aux_output_scale', value=2.0, unit='V', ch=0, get_cmd='/auxouts/%(ch)d/scale'),
        QReal('Aux_output_offset', value=0.0, unit='V', ch=0, get_cmd='/auxouts/%(ch)d/offset'),
    ]
    
       
    def __init__(self, **kw):
        BaseDriver.__init__(self, **kw)
        self.deviceID=kw['deviceID']
        self.n_ch = 2
        self.wave = {}
        self._node_datatypes = {}
        self.aux_n_ch = 4
        self.aux_out = False

    def performOpen(self, **kw):
        """Perform the operation of opening the instrument connection"""
        # connect through deviceID
        apilevel = 6  # The API level supported by this driver
        (daq, device, props) = zhinst.utils.create_api_session(self.deviceID, apilevel, 
                                                               required_devtype='UHF', 
                                                               required_options=['AWG'])
        zhinst.utils.api_server_version_check(daq)
        # Create a base configuration: Disable all available outputs, awgs, demods, scopes,...
        zhinst.utils.disable_everything(daq, device)
        self.daq = daq
        self.device = device
        self.props = props
        

    def performClose(self, **kw):
        """Perform the close instrument connection operation"""
        # do not check for error if close was called with an error
        try:
            base = '/%s/awgs/0/' % self.device
            self.daq.setInt(base + 'enable', 0)
        except Exception:
            # never return error here
            pass


    def init(self):
        # Create a base configuration: Disable all available outputs, awgs, demods, scopes,...
        zhinst.utils.disable_everything(self.daq, self.device)


    def performSetValue(self, quant, value, ch=0):
        """Perform the Set Value instrument operation. This function should
        return the actual value set by the instrument"""
        # update value, necessary since we later use getValue to get config
        quant.setValue(value)
        quant.ch=ch
        # set node parameters
        if quant.get_cmd != '':
            if quant.type == 'Option':
                value_set = self._set_node_value(quant, dict(quant.options)[value])
            else:
                value_set = self._set_node_value(quant, value)
        return value_set


    def create_waveform(self, length=0, aux_length=0):
        # re_init AWG for clearing the wave in used
        #self.init()
        
        # map wave to channel
        self._map_wave_to_channel()
        
        # proceed depending on run mode
        run_mode = self._get_node_value(self.quantities['RunMode'])
        
        # create waveforms, one per channel
        awg_program = '' 
        for channel in range(self.n_ch):
            awg_program += textwrap.dedent("""\
            wave w%d = zeros(_N_)+1;
            """) % (channel)
        # if needs aux output, create aux waveform for aux channel
        if self.aux_out:
            for channel in range(self.aux_n_ch):
                awg_program += textwrap.dedent("""\
                wave aux_w%d = zeros(_AUX_N_);
                """) % (channel)
            # continue mode (internal trigger mode)
            if run_mode == 1:
                awg_program += textwrap.dedent("""\
                    setUserReg(0, 0);
                    while(true){
                        while(getUserReg(0) == 0){
                            playWave(%s);
                            playAuxWave(%s);
                            }
                        }""") % (self.wave_to_channel, self.aux_wave_to_channel)
            elif run_mode == 0:
                awg_program += textwrap.dedent("""\
                    setUserReg(0, 0);
                    while(true){
                        waitDigTrigger(1,1);
                        playWave(%s);
                        playAuxWave(%s);
                        }""") % (self.wave_to_channel, self.aux_wave_to_channel)
            
            # Replace the placeholder with the length of points.
            awg_program = awg_program.replace('_AUX_N_', str(aux_length))
        else:
            # continue mode (internal trigger mode)
            if run_mode == 1:
                awg_program += textwrap.dedent("""\
                    setUserReg(0, 0);
                    while(true){
                        while(getUserReg(0) == 0){
                            playWave(%s);
                            }
                        }""") % (self.wave_to_channel)
            elif run_mode == 0:
                awg_program += textwrap.dedent("""\
                    setUserReg(0, 0);
                    while(true){
                        waitDigTrigger(1,1);
                        playWave(%s);
                        }""") % (self.wave_to_channel)
            
        # Replace the placeholder with the length of points.
        awg_program = awg_program.replace('_N_', str(length))
        # stop current AWG
        base = '/%s/awgs/0/' % (self.device)
        self.daq.setInt(base + 'enable', 0)
        # compile and upload
        self._upload_awg_program(awg_program, core=0)
    
    
    def update_waveform(self, points, name='ABC'):
        self.wave[name] = points
        
        
    def use_waveform(self, name):
        # 'name' should be the type of name=['name0','name1','aux_name0','aux_name1',...]
        # 'name0' and 'name1' should be the same as in 'update_waveform' and will map to ch=0 and ch=1
        # 'aux_name0' and 'aux_name1' ... should be the same as in 'update_waveform' and will map to aux_ch=0 and aux_ch=1 ...
        # stop current AWG
        base = '/%s/awgs/0/' % (self.device)
        self.daq.setInt(base + 'enable', 0)
        
        # get waveform
        wave_length = len(self.wave[name[0]])
        waveform = np.zeros(wave_length*self.n_ch)
        for n in range(self.n_ch):
            waveform[n:wave_length*self.n_ch:self.n_ch] = self.wave[name[n]]
        
        # Replace the waveform with 'points'.
        waveform_native = zhinst.utils.convert_awg_waveform(waveform)
        waveform_node_path = '/%s/awgs/0/waveform/waves/0' % (self.device)
        self.daq.setVector(waveform_node_path, waveform_native)
        
        # if needs aux output, use aux waveform for aux channel
        if self.aux_out:
            # set aux channel
            for ch in range(self.aux_n_ch):
                self.setValue('Aux_output_select', 'AWG', ch=ch)
                self.setValue('Aux_demod_select', 'aux_ch%d' % (ch), ch=ch)
                self.setValue('Aux_output_scale', 2.0, ch=ch)
                self.setValue('Aux_output_offset', 0.0, ch=ch)
            # get aux waveform
            aux_wave_length = len(self.wave[name[self.n_ch]])
            aux_waveform = np.zeros(aux_wave_length*self.aux_n_ch)
            for n in range(self.aux_n_ch):
                aux_waveform[n:aux_wave_length*self.aux_n_ch:self.aux_n_ch] = self.wave[name[n+self.n_ch]]
            # Replace the aux waveform with 'points'.
            aux_waveform_native = zhinst.utils.convert_awg_waveform(aux_waveform)
            aux_waveform_node_path = '/%s/awgs/0/waveform/waves/1' % (self.device)
            self.daq.setVector(aux_waveform_node_path, aux_waveform_native)
        
        # Start the AWG in single-shot mode.
        # This is the preferred method of using the AWG: Run in single mode continuous waveform playback is best achieved by
        # using an infinite loop (e.g., while (true)) in the sequencer program.
        self.daq.setInt(base + 'single', 1)
        self.daq.setInt(base + 'enable', 1)
        self.daq.sync()
    
    
    def performGetValue(self, quant, **kw):
        """Perform the Set Value instrument operation. This function should
        return the actual value set by the instrument"""
        if quant.get_cmd != '':
            value = self._get_node_value(quant)
        else:
            # for all others, return local value
            value = quant.getValue()
        return value


    def _map_wave_to_channel(self):
        """Create map between waveform in use and corresponding output channels"""
        x = []
        for n in range(self.n_ch):
            x.append('w%d' % (n))
        self.wave_to_channel = ', '.join(x)
        aux = []
        for n in range(self.aux_n_ch):
            aux.append('aux_w%d' % (n))
        self.aux_wave_to_channel = ', '.join(aux)
        

    def _upload_awg_program(self, awg_program, core=0):
        # Transfer the AWG sequence program. Compilation starts automatically.
        # Create an instance of the AWG Module
        awgModule = self.daq.awgModule()
        awgModule.set('awgModule/device', self.device)
        awgModule.set('awgModule/index', int(core))
        awgModule.execute()
        awgModule.set('awgModule/compiler/sourcestring', awg_program)
        while awgModule.getInt('awgModule/compiler/status') == -1:
            time.sleep(0.1)

        if awgModule.getInt('awgModule/compiler/status') == 1:
            # compilation failed, raise an exception
            assert True, 'Upload failed:\n' + awgModule.getString('awgModule/compiler/statusstring')

        # Wait for the waveform upload to finish
        time.sleep(0.1)
        while ((awgModule.getDouble('awgModule/progress') < 1.0) and
                (awgModule.getInt('awgModule/elf/status') != 1)):
            time.sleep(0.1)

        if awgModule.getInt('awgModule/elf/status') == 1:
            assert True, 'Uploading the AWG program failed.'


    def _get_node_value(self, quant):
        """Get instrument value using ZI node hierarchy"""
        # get node definition
        node = self._get_node(quant)
        dtype = self._get_node_datatype(node)
        # read data from ZI
        d = self.daq.get(node, True)
        if len(d) == 0:
            assert True, 'No value defined at node %s.' % node
        # extract and return data
        data = next(iter(d.values()))
        # if returning dict, strip timing information (API level 6)
        if isinstance(data, dict) and 'value' in data:
            data = data['value']
        value = dtype(data[0])
        return value


    def _set_node_value(self, quant, value):
        """Set value of quantity using ZI node hierarchy"""
        # get node definition and datatype
        node = self._get_node(quant)
        dtype = self._get_node_datatype(node)
        self._set_parameter(node, dtype(value))
        # read actual value set by the instrument
        value = self._get_node_value(quant)
        return value


    def _set_parameter(self, node, value):
        """Set value for given node"""
        if isinstance(value, float):
            # self.daq.setDouble(node, value)
            self.daq.asyncSetDouble(node, value)
        elif isinstance(value, int):
            # self.daq.setInt(node, value)
            self.daq.asyncSetInt(node, value)
        elif isinstance(value, str):
            # self.daq.setString(node, value)
            self.daq.asyncSetString(node, value)
        elif isinstance(value, complex):
            self.daq.setComplex(node, value)


    def _get_node(self, quant):
        """Get node string for quantity"""
        if '%(ch)d' in quant.get_cmd:
            get_cmd = quant.get_cmd % dict(ch=quant.ch)
        else:
            get_cmd = quant.get_cmd
        return '/' + self.device + get_cmd


    def _get_node_datatype(self, node):
        """Get datatype for object at node"""
        # used cached value, if available
        if node in self._node_datatypes:
            return self._node_datatypes[node]
        # find datatype from returned data
        d = self.daq.get(node, True)
        if len(d) == 0:
            assert True, 'No value defined at node %s.' % node

        data = next(iter(d.values()))
        # if returning dict, strip timing information (API level 6)
        if isinstance(data, dict) and 'value' in data:
            data = data['value']
        # get first item, if python list assume string
        if isinstance(data, list):
            dtype = str
        # not string, should be np array, check dtype
        elif data.dtype in (int, np.int_, np.int64, np.int32, np.int16):
            dtype = int
        elif data.dtype in (float, np.float_, np.float64, np.float32):
            dtype = float
        elif data.dtype in (complex, np.complex_, np.complex64, np.complex128):
            dtype = complex
        else:
            assert True, 'Undefined datatype for node %s.' % node

        # keep track of datatype for future use
        self._node_datatypes[node] = dtype
        return dtype
    
    
    def data_acquire_set(self, length=4096, samplerate='900M', trigdelay=0, trigchannel='TrigIn1', singnalrange=1.0,
                         signaldict={'signalinput1': 0, 'signalinput2': 1}, mode='Triggered', **kw):
        # length should be multiple of 4096
        # set Sig input
        self.daq.setInt('/%s/scopes/0/channel' % (self.device), 3) # '1' for only one input, '3' for two inputs
        for sig in signaldict:
            self.setValue('Sig_In_Channel', sig, ch=signaldict[sig])
            self.setValue('Sig_In_Imp50', 'ON', ch=signaldict[sig])
            self.setValue('Sig_In_AC', 'ON', ch=signaldict[sig])
            self.setValue('Sig_In_Range', singnalrange, ch=signaldict[sig])
        self.setValue('Sig_In_SampleRate', samplerate)
        self.setValue('Sig_In_RunMode', mode)
        self.setValue('Sig_In_Diffmode', 'OFF')
        
        # Disable the scope.
        self.daq.setInt('/%s/scopes/0/enable' % self.device, 0)
        # set record length
        self.setValue('Record_length', length)
        
        # set trigger
        self.setValue('Sig_In_TrigEnable', 'enable')
        self.setValue('Sig_In_TrigChannel', trigchannel)
        self.setValue('Sig_In_TrigSlope', 'Rise')
        self.setValue('Sig_In_TrigLevel', 0.1)
        self.setValue('Sig_In_TrigDelay', trigdelay)
        # set trighysteresis in case of noise
        self.daq.setDouble('/%s/scopes/0/trighysteresis/mode' % self.device, 0)
        self.daq.setDouble('/%s/scopes/0/trighysteresis/relative' % self.device, 0.025)
                
        
    def acquire_single_record(self):
        # Set up the Scope Module.
        scopeModule = self.daq.scopeModule()
        scopeModule.set('mode', 1)
        scopeModule.subscribe('/%s/scopes/0/wave' % self.device)
        self.daq.setInt('/%s/scopes/0/single' % self.device, 1)
        scopeModule.execute()
        
        # Start the scope...
        self.daq.setInt('/%s/scopes/0/enable' % self.device, 1)
        self.daq.sync()
        time.sleep(0.005)
        # Read the scope data with timeout.
        local_timeout = 1.0
        records = 0
        while (records < 1) and (local_timeout > 0):
            time.sleep(0.05)
            local_timeout -= 0.05
            records = scopeModule.getInt("records")
        # Disable the scope.
        self.daq.setInt('/%s/scopes/0/enable' % self.device, 0)

        data_read = scopeModule.read(True)
        wave_nodepath = '/{}/scopes/0/wave'.format(self.device)
        assert wave_nodepath in data_read, "Error: The subscribed data `{}` was returned.".format(wave_nodepath)
        data = data_read[wave_nodepath][0][0]
        
        # all result data is in data['wave']
        # get record data as real time, it is not necessary
        """
        f_s = 0.9e9  # sampling rate of scope and AWG
        for n in range(0, len(data['channelenable'])):
            p = data['channelenable'][n]
            if p:
                y_measured = data['wave'][n]
                x_measured = np.arange(-data['totalsamples'], 0)*data['dt'] + \
                    (data['timestamp'] - data['triggertimestamp'])/f_s
        """
        return data['wave']