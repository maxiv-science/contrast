from .Detector import Detector, SoftwareLiveDetector, TriggeredDetector, BurstDetector
from ..environment import env

import time
import numpy as np
import os
from h5py import ExternalLink
import requests
import json
import zmq
import threading

class StreamReceiver:
    """
    Helper class for the Eiger.
    """
    def __init__(self, receiver_ip, receiver_port=9997):
        self.context = zmq.Context()
        self.req_socket = self.context.socket(zmq.REQ)
        self.req_socket.connect('tcp://%s:%u' % (receiver_ip, receiver_port))

    def arm(self, filename, shape, dtype):
        self.req_socket.send_json({'command': 'arm',
                                   'filename': filename,
                                   'type': dtype,
                                   'shape': shape})
        print('send msg')
        if self.req_socket.poll(1000):
            print(self.req_socket.recv())
            return True
        else:
            return False


class Eiger(Detector, SoftwareLiveDetector, TriggeredDetector, BurstDetector):

    def __init__(self, name=None, ip_address='172.16.126.91', api_version='1.8.0',
                 shape=[2068, 2162], receiver_ip=''):
        """
        Class to interact directly with the Eiger Simplon API.
        """
        self.dcu_ip = ip_address
        self.receiver_ip = receiver_ip
        self.api_version = api_version
        self._hdf_path_base = 'entry_%04d/measurement/Eiger/data'
        self.shape = shape
        Detector.__init__(self, name=name)
        SoftwareLiveDetector.__init__(self)
        TriggeredDetector.__init__(self)
        BurstDetector.__init__(self)

    def initialize(self):
        self.session = requests.Session()
        self.session.trust_env = False
        self.receiver = StreamReceiver()

        # set up the detector
        self._set('detector', 'config/threshold/1/mode', 'enabled')
        self._set('detector', 'config/threshold/2/mode', 'disabled')
        self._set('stream', 'config/mode', 'enabled')
        self._set('filewriter', 'config/mode', 'disabled')
        self._set('monitor', 'config/mode', 'enabled')

    def _get(self, subsystem, key):
        response = self.session.get('http://%s/%s/api/%s/%s' %(self.dcu_ip, subsystem, self.api_version, key))
        if response:
            if response.headers['content-type'] == 'application/json':
                return response.json()
            else:
                print('unkown response type', response.headers['content-type'])
        else:
            print('error')
            print(response)

    def _set(self, subsystem, key, value=None):
        url = 'http://%s/%s/api/%s/%s' %(self.dcu_ip, subsystem, self.api_version, key)
        if value:
            payload = {'value': value}
        else:
            payload = None
        response = self.session.put(url, json=payload)
        if response.status_code != 200:
            print(response.text)

    def busy(self):
        return not self._get('detector', 'status/state')['value'] == 'idle'

    @property
    def compression(self):
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
        return self._get('detector', 'config/photon_energy')['value']

    @energy.setter
    def energy(self, val):
        self._set('detector', 'config/photon_energy', float(val))

    @property
    def threshold(self):
        return self._get('detector', 'config/threshold/1/energy')['value']

    @threshold.setter
    def threshold(self, val):
        self._set('detector', 'config/threshold/1/energy', float(val))

    def prepare(self, acqtime, dataid, n_starts):
        """
        Run before acquisition, once per scan. Set up triggering,
        number of images etc.
        """
        self._set('detector', 'config/nimages', self.burst_n)
        self._set('detector', 'config/count_time', acqtime)
        self._set('detector', 'config/count_time', acqtime+1e-6)
        if self.hw_trig:
            self._set('detector', 'config/trigger_mode', 'exts')
            self._set('detector', 'config/ntrigger', self.hw_trig_n)
        else:
            self._set('detector', 'config/trigger_mode', 'ints')
        filename = 'scan_%06d_%s.hdf5' % (dataid, self.name)
        path = os.path.join(env.paths.directory, filename)
        self.dpath = path
        self.dtype = 'uint%u' % self._get('detector', 'config/bit_depth_image')['value']

    def arm(self):
        """
        Start the detector if hardware triggered, just prepareAcq otherwise.
        """
        if not self.receiver.arm(self.dpath, self.shape, self.dtype):
            raise Exception('Bad things happened here')
        self._set('detector', 'command/arm')

    def start(self):
        """
        Start acquisition when software triggered.
        """
        if not self.hw_trig:
            raise NotImplementedError
            self._set('detector', 'command/trigger') # BLOCKS! FIX.
            self._set('detector', 'command/disarm')

    def stop(self):
        raise NotImplementedError

    def read(self):
        return ExternalLink(self.dpath , self._hdf_path_base % self.arm_number)

