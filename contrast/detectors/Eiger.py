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


class Eiger(Detector, SoftwareLiveDetector, TriggeredDetector, BurstDetector):
    """
    Provides a direct interface to the Dectris Eiger server.
    """

    def __init__(self, name=None, host='b-nanomax-eiger-dc-1.maxiv.lu.se',
                 api_version='1.8.0', use_image_appendix=False):
        """
        Class to interact directly with the Eiger Simplon API.
        """
        self.host = host
        self.api_version = api_version
        self._hdf_path = 'entry/instrument/eiger/data'
        self.acqthread = None
        self.use_image_appendix = use_image_appendix
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
        return self._get('detector', 'config/photon_energy')['value'] / 1000

    @energy.setter
    def energy(self, val):
        if (val < 4) or (val > 30):
            print('Bad energy value, should be in keV and between 4-30')
            return
        val = float(val) * 1000
        self._set('detector', 'config/photon_energy', val)

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
