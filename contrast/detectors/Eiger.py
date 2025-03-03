from .Detector import (
    Detector, SoftwareLiveDetector, TriggeredDetector, BurstDetector)
from ..recorders.Hdf5Recorder import Link
from ..environment import env

import time
import numpy as np
import os
import requests
import json
import zmq
from threading import Thread
from base64 import b64encode, b64decode
try:
    import tango
except ImportError:
    pass


class Eiger(Detector, SoftwareLiveDetector, TriggeredDetector, BurstDetector):
    """
    Provides a direct interface to the Dectris Eiger server.
    """

    def __init__(self, name=None, host='b-nanomax-eiger-dc-1.maxiv.lu.se',
                 api_version='1.8.0', use_image_appendix=False,
                 hdf_path='entry/instrument/Eiger/data',
                 hw_trig_min_latency=100e-9):
        """
        Class to interact directly with the Eiger Simplon API.
        """
        self.host = host
        self.api_version = api_version
        self._hdf_path = hdf_path
        self.acqthread = None
        self.use_image_appendix = use_image_appendix
        self.hw_trig_min_latency = hw_trig_min_latency
        Detector.__init__(self, name=name)
        SoftwareLiveDetector.__init__(self)
        TriggeredDetector.__init__(self)
        BurstDetector.__init__(self)

    def initialize(self):
        self.session = requests.Session()
        self.session.trust_env = False
        self.burst_latency = 100e-9

        # set up the detector
        self._set('detector', 'command/disarm')
        self._set('detector', 'command/cancel')  # who knows
        self._set('detector', 'config/threshold/1/mode', 'enabled')
        self._set('detector', 'config/threshold/2/mode', 'disabled')
        self._set('stream', 'config/mode', 'enabled')
        self._set('filewriter', 'config/mode', 'disabled')
        self._set('monitor', 'config/mode', 'enabled')
        self._set('stream', 'config/header_detail', 'all')
        self._set('detector', 'config/counting_mode', 'retrigger')

    def _get(self, subsystem, key, timeout=3.0):
        response = self.session.get(
            'http://%s/%s/api/%s/%s' % (
                self.host, subsystem, self.api_version, key),
            timeout=timeout)
        if response:
            if 'application/json' in response.headers['content-type']:
                return response.json()
            else:
                print('unkown response type', response.headers['content-type'])
        else:
            print('error')
            print(response)

    def _set(self, subsystem, key, value=None, timeout=3.0):
        url = 'http://%s/%s/api/%s/%s' % (
            self.host, subsystem, self.api_version, key)
        if value is None:
            payload = None
        else:
            payload = {'value': value}
        response = self.session.put(url, json=payload, timeout=timeout)
        if response.status_code != 200:
            print(response.text)

    def busy(self):
        if self.acqthread and self.acqthread.is_alive():
            return True
        return not self._get(
            'detector', 'status/state')['value'] in ('idle', 'ready')

    @property
    def max_count_rate(self):
        """ Maximum count rate according to the server """
        val = self._get(
            'detector', 'config/countrate_correction_count_cutoff')['value']
        return int(val)

    @property
    def compression(self):
        """ Whether bitshuffle compression is enabled """
        val = self._get('detector', 'config/compression')['value']
        return val == 'bslz4'

    @compression.setter
    def compression(self, val):
        if val:
            self._set('detector', 'config/compression', 'bslz4')
        else:
            self._set('detector', 'config/compression', 'none')

    @property
    def energy(self):
        """ Operating energy in keV """
        return self._get('detector', 'config/photon_energy')['value']

    @energy.setter
    def energy(self, val):
        if (val < 4000) or (val > 30000):
            print('Bad energy value, should be in between 4000 eV and 30000 eV')
            return
        val = float(val)
        self._set('detector', 'config/photon_energy', val)
        print(f'energy of {self.name} has been set to {self.energy} eV')

    @property
    def mask_applied(self):
        """ Whether to apply the mask """
        return self._get('detector', 'config/pixel_mask_applied')['value']

    @mask_applied.setter
    def mask_applied(self, val):
        self._set('detector', 'config/pixel_mask_applied', val)

    @property
    def pixel_splitting(self):
        """ Whether to use virtual pixel splitting """
        return self._get(
            'detector', 'config/virtual_pixel_correction_applied')['value']

    @pixel_splitting.setter
    def pixel_splitting(self, val):
        self._set('detector', 'config/virtual_pixel_correction_applied', val)

    @property
    def threshold(self):
        """ Energy threshold for the counters """
        return self._get('detector', 'config/threshold/1/energy')['value']

    @threshold.setter
    def threshold(self, val):
        self._set('detector', 'config/threshold/1/energy', float(val))

    def prepare(self, acqtime, dataid, n_starts):
        BurstDetector.prepare(self, acqtime, dataid, n_starts)
        self._set('detector', 'config/nimages', self.burst_n)
        self._set('detector', 'config/frame_time',
                  self.acqtime + self.burst_latency)
        self._set('detector', 'config/count_time', self.acqtime)
        if self.hw_trig:
            self._set('detector', 'config/trigger_mode', 'exts')
            self._set('detector', 'config/ntrigger',
                      int(self.hw_trig_n * n_starts))
        else:
            self._set('detector', 'config/trigger_mode', 'ints')
            # np.int64 isn't json serializable:
            self._set('detector', 'config/ntrigger', int(n_starts))
        if dataid is None:
            self.dpath = ''
        else:
            filename = 'scan_%06d_%s.hdf5' % (dataid, self.name)
            self.dpath = os.path.join(env.paths.directory, filename)
            if os.path.exists(self.dpath):
                print('%s: this hdf5 file exists, I am raising an error now'
                      % self.name)
                raise Exception('%s hdf5 file already exists' % self.name)
        self._set('stream', 'config/header_appendix',
                  json.dumps({'filename': self.dpath}))
        if self.use_image_appendix: # for CoSAXS tango server
            self._set('stream', 'config/image_appendix',
                      json.dumps({'filename': self.dpath}))
        self._set('detector', 'command/arm')
        self.n_started = 0

    def arm(self):
        # The Eiger is armed only once.
        pass

    def start(self):
        self.n_started += 1
        if not self.hw_trig:
            self.acqthread = Thread(target=self._set,
                                    args=('detector', 'command/trigger'),
                                    kwargs={'timeout': None})
            self.acqthread.start()

    def stop(self):
        # there's also cancel - not sure which to use:
        self._set('detector', 'command/disarm')

    def read(self):
        if self.dpath:
            ret = {'frames': Link(self.dpath, self._hdf_path, universal=True),
                   'thumbs:': None}
        else:
            ret = None
        return ret

    def _start(self, acqtime):
        """
        The Eiger needs to override this method as it uses software triggers.
        """
        self.stopped = False
        NN = 1000
        while not self.stopped:
            self.prepare(acqtime, None, NN)
            for nn in range(NN):
                if self.stopped:
                    self.stop()
                    break
                self.arm()
                self.start()
                while self.busy():
                    time.sleep(.05)

    def get_mask(self):
        """
        Get the Eiger mask, taken from the example in the manual.
        """
        darray = self._get(
            'detector', 'config/pixel_mask', timeout=15)['value']
        dtype = np.dtype(str(darray['type']))
        shape = darray['shape']
        mask = np.frombuffer(
            b64decode(darray['data']), dtype=dtype).reshape(shape)
        return mask.copy()

    def set_mask(self, array):
        """
        Set the Eiger mask, also adapted from the manual.
        """
        data = {'__darray__': (1, 0, 0),
                'type': array.dtype.str,
                'shape': array.shape,
                'filters': ['base64'],
                'data': b64encode(array.data).decode('ascii')}
        self._set('detector', 'config/pixel_mask', data, timeout=15)

        # arming and disarming stores it:
        self._set('detector', 'command/arm')
        self._set('detector', 'command/disarm')


class EigerTango(Detector, SoftwareLiveDetector, TriggeredDetector, BurstDetector):
    """
    Provides a direct interface to the Dectris Eiger server via a Tango Server.
    """

    def __init__(self, device_name, name=None,
                 #api_version='1.8.0', use_image_appendix=False,
                 hdf_path='entry/instrument/Eiger/data',
                 rotation=0,
                 hw_trig_min_latency=100e-9):
        """
        Class to interact directly with the Eiger Simplon API.
        """
        self.proxy = tango.DeviceProxy(device_name)
        self.proxy.set_timeout_millis(10000)
        self.acqthread = None
        self._hdf_path = hdf_path
        self.name = name
        self.rotation = rotation
        self.hw_trig_min_latency = hw_trig_min_latency
        self.host = self._get_tango_property('dcu_host')
        self.api_version = self._get_tango_property('api_version')
        Detector.__init__(self, name=name)
        SoftwareLiveDetector.__init__(self)
        TriggeredDetector.__init__(self)
        BurstDetector.__init__(self)

    def initialize(self):
        self.session = requests.Session()
        self.session.trust_env = False
        self.burst_latency = 100e-9
        self.n_started = 0
        print(f"{self.name}: Initilazing the Tango Server...", end="")
        self.proxy.Init()
        print(f" done.")
    
    def _get_tango_property(self, property: str):
        '''helper function to easily read properties from the Tango servers'''
        raw = self.proxy.get_property([property])
        ret = raw[property][0] # unpack the response
        return ret
    
    def _get(self, subsystem, key, timeout=3.0):
        response = self.session.get(
            'http://%s/%s/api/%s/%s' % (
                self.host, subsystem, self.api_version, key),
            timeout=timeout)
        if response:
            if 'application/json' in response.headers['content-type']:
                return response.json()
            else:
                print('unkown response type', response.headers['content-type'])
        else:
            print('error')
            print(response)

    def _set(self, subsystem, key, value=None, timeout=3.0):
        url = 'http://%s/%s/api/%s/%s' % (
            self.host, subsystem, self.api_version, key)
        if value is None:
            payload = None
        else:
            payload = {'value': value}
        response = self.session.put(url, json=payload, timeout=timeout)
        if response.status_code != 200:
            print(response.text)

    def busy(self):
        # if self.proxy.State() == tango.DevState.RUNNING:
        #     return True
        # else:
        #     return False
        # We cannot rely purly on the nFramesReceived attribute, as it is not reset at the end of an acquisition
        # so we check the State first, to see if it is idle
        if self.proxy.State() == tango.DevState.STANDBY:
            return False
        if self.proxy.nFramesReceived < self.n_started*self.burst_n:
            return True
        else:
            return False

    @property
    def max_count_rate(self):
        """ Maximum count rate according to the server """
        val = self._get(
            'detector', 'config/countrate_correction_count_cutoff')['value']
        return int(val)

    @property
    def energy(self):
        """ Operating energy in eV """
        return self.proxy.Energy

    @energy.setter
    def energy(self, val):
        if (val < 4000) or (val > 30000):
            print('Bad energy value, should be in between 4000 eV and 30000 eV')
            return
        val = float(val)
        self.proxy.Energy = val
        print(f'energy of {self.name} has been set to {self.energy} eV')

    @property
    def mask_applied(self):
        """ Whether to apply the mask """
        return self._get('detector', 'config/pixel_mask_applied')['value']

    @mask_applied.setter
    def mask_applied(self, val):
        self._set('detector', 'config/pixel_mask_applied', val)

    @property
    def pixel_splitting(self):
        """ Whether to use virtual pixel splitting """
        return self._get(
            'detector', 'config/virtual_pixel_correction_applied')['value']

    @pixel_splitting.setter
    def pixel_splitting(self, val):
        self._set('detector', 'config/virtual_pixel_correction_applied', val)

    @property
    def threshold(self):
        """ Energy threshold for the counters """
        return self.proxy.Threshold

    @threshold.setter
    def threshold(self, val):
        self.proxy.Threshold = val
        
    @property
    def rotation(self):
        """Rotation of detector frame. Uses numpy.rot90() notation."""
        print(f"{self.name}: Frame rotation (in numpy.rot90() notation): {self.proxy.Rotation}")
        return self.proxy.Rotation
    
    @rotation.setter
    def rotation(self, val):
        self.proxy.Rotation = int(val)
        print(f"{self.name}: Frame rotation (in numpy.rot90() notation): {self.proxy.Rotation}")

    def prepare(self, acqtime, dataid, n_starts):
        BurstDetector.prepare(self, acqtime, dataid, n_starts)
        acqtime = self.acqtime
        
        if self.busy():
            raise Exception(f'{self.name} is busy!')
        
        self.proxy.nFramesPerTrigger = self.burst_n
        
        self.proxy.FrameTime = acqtime + self.burst_latency
        self.proxy.ExposureTime = acqtime
        self.repetitions = self.hw_trig_n if self.hw_trig else 1        
            
        if (dataid is None) or (env.paths.directory is None):
            self.dpath = ''
        else:
            path = env.paths.directory
            filename = 'scan_%06d_%s.hdf5' % (dataid, self.name)
            self.dpath = os.path.join(env.paths.directory, filename)
            if os.path.exists(self.dpath):
                print('%s: this hdf5 file exists, I am raising an error now'
                      % self.name)
                raise Exception('%s hdf5 file already exists' % self.name)
        self.proxy.DestinationFilename = self.dpath
        if self.hw_trig:
            self.proxy.TriggerMode = 'EXTERNAL_MULTI'
            self.proxy.nTriggers = self.hw_trig_n * n_starts
            
        else:
            self.proxy.TriggerMode = 'INTERNAL'
            self.proxy.nTriggers = n_starts
            self.proxy.nFramesPerTrigger = self.burst_n
            
        self.proxy.Arm()
        self.n_started = 0

    def arm(self):
        # The Eiger is armed only once.
        pass

    def start(self):
        self.n_started += self.repetitions
        if not self.hw_trig:
            self.proxy.Trigger()

    def stop(self):
        self.proxy.Stop()
        self.n_started = 0

    def read(self):
        if self.dpath:
            ret = {'frames': Link(self.dpath, self._hdf_path, universal=True),
                   'thumbs:': None}
        else:
            ret = None
        return ret

    def start_live(self, acqtime):
        # for now, the Tango DS does not support variable exposure times for the live mode. Live mode is hardcoded to 1 s.
        self.proxy.Live()
        
    def stop_live(self):
        self.stop()
        
    def get_mask(self):
        """
        Get the Eiger mask, taken from the example in the manual.
        """
        darray = self._get(
            'detector', 'config/pixel_mask', timeout=15)['value']
        dtype = np.dtype(str(darray['type']))
        shape = darray['shape']
        mask = np.frombuffer(
            b64decode(darray['data']), dtype=dtype).reshape(shape)
        return mask.copy()

    def set_mask(self, array):
        """
        Set the Eiger mask, also adapted from the manual.
        """
        data = {'__darray__': (1, 0, 0),
                'type': array.dtype.str,
                'shape': array.shape,
                'filters': ['base64'],
                'data': b64encode(array.data).decode('ascii')}
        self._set('detector', 'config/pixel_mask', data, timeout=15)

        # arming and disarming stores it:
        self._set('detector', 'command/arm')
        self._set('detector', 'command/disarm')


class SelunTango(EigerTango):
    """
    Provides a direct interface to the Dectris SELUN server via a Tango Server.
    """

    @property
    def OnDetectorBinning(self):
        """ Energy threshold for the counters """
        return self.proxy.OnDetectorBinning

    @OnDetectorBinning.setter
    def OnDetectorBinning(self, val):
        """ Energy threshold for the counters """
        self.proxy.OnDetectorBinning = val
