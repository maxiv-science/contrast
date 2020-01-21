"""
This currently arms the eiger on every software step, which is sub-optimal. To be fixed
later, but the receiver has to be updated too.
"""

from .Detector import Detector, SoftwareLiveDetector, TriggeredDetector, BurstDetector
from ..environment import env

import time
import numpy as np
import os
from h5py import ExternalLink
import requests
import json
import zmq
from threading import Thread

class StreamReceiver:
    """
    Helper class for the Eiger.
    """
    def __init__(self, receiver_ip):
        self.context = zmq.Context()
        self.req_socket = self.context.socket(zmq.REQ)
        self.req_socket.connect('tcp://%s:9997' %receiver_ip)
    
    def prepare(self, filename):
        self.req_socket.send_json({'command': 'prepare', 
                                   'filename': filename})
#        print('send msg')
        if self.req_socket.poll(10000):
            self.req_socket.recv()
            return True
        else:
            return False

class Eiger(Detector, SoftwareLiveDetector, TriggeredDetector, BurstDetector):

    def __init__(self, name=None, ip_address='172.16.126.91', api_version='1.8.0',
                 shape=[2068, 2162], receiver_ip='172.18.1.245'):
        """
        Class to interact directly with the Eiger Simplon API.
        """
        self.dcu_ip = ip_address
        self.receiver_ip = receiver_ip
        self.api_version = api_version
        self._hdf_path_base = 'entry_%04d/measurement/Eiger/data'
        self.shape = shape
        self.acqthread = None
        Detector.__init__(self, name=name)
        SoftwareLiveDetector.__init__(self)
        TriggeredDetector.__init__(self)
        BurstDetector.__init__(self)

    def initialize(self):
        self.session = requests.Session()
        self.session.trust_env = False
        self.receiver = StreamReceiver(self.receiver_ip)

        # set up the detector
        self._set('detector', 'command/disarm')
        self._set('detector', 'command/cancel') # who knows
        self._set('detector', 'config/threshold/1/mode', 'enabled')
        self._set('detector', 'config/threshold/2/mode', 'disabled')
        self._set('stream', 'config/mode', 'enabled')
        self._set('filewriter', 'config/mode', 'disabled')
        self._set('monitor', 'config/mode', 'enabled')
        self._set('stream', 'config/header_detail', 'all')
        self._set('detector', 'config/counting_mode', 'retrigger')

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
        if value is None:
            payload = None
        else:
            payload = {'value': value}
        response = self.session.put(url, json=payload)
        if response.status_code != 200:
            print(response.text)

    def busy(self):
        if self.acqthread and self.acqthread.is_alive():
            return True            
        return not self._get('detector', 'status/state')['value'] in ('idle', 'ready')

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
        return self._get('detector', 'config/photon_energy')['value'] / 1000

    @energy.setter
    def energy(self, val):
        if (val < 4) or (val > 30):
            print('Bad energy value, should be in keV and between 4-30')
            return
        val = float(val)*1000
        self._set('detector', 'config/photon_energy', val)

    @property
    def mask_applied(self):
        return self._get('detector', 'config/pixel_mask_applied')['value']

    @mask_applied.setter
    def mask_applied(self, val):
        self._set('detector', 'config/pixel_mask_applied', val)

    @property
    def pixel_splitting(self):
        return self._get('detector', 'config/virtual_pixel_correction_applied')['value']

    @pixel_splitting.setter
    def pixel_splitting(self, val):
        self._set('detector', 'config/virtual_pixel_correction_applied', val)

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
        self._set('detector', 'config/frame_time', acqtime)
        self._set('detector', 'config/count_time', acqtime - 100.0e-9)
        if self.hw_trig:
            self._set('detector', 'config/trigger_mode', 'exts')
            self._set('detector', 'config/ntrigger', self.hw_trig_n)
        else:
            self._set('detector', 'config/trigger_mode', 'ints')
##            self._set('detector', 'config/ntrigger', n_starts)
            self._set('detector', 'config/ntrigger', 1) ### temporary
        if dataid is None:
            self.dpath = ''
        else:
            filename = 'scan_%06d_%s.hdf5' % (dataid, self.name)
            path = os.path.join(env.paths.directory, filename)
            self.dpath = path
        self.dtype = 'uint%u' % self._get('detector', 'config/bit_depth_image')['value']
##        self._set('detector', 'command/arm')
        self.arm_number = -1

    def arm(self):
        """
        Start the detector if hardware triggered, just prepareAcq otherwise.
        """
        if not self.receiver.prepare(filename=self.dpath):
            raise Exception('The zmq receiver is broken')
        self._set('detector', 'command/arm') 
        self.arm_number += 1

    def start(self):
        """
        Start acquisition when software triggered.
        """

        if not self.hw_trig:
            self.acqthread = Thread(target=self._set, args=('detector', 'command/trigger'))
            self.acqthread.start()

    def stop(self):
        self._set('detector', 'command/disarm') # there's also cancel - not sure which to use

    def read(self):
        return ExternalLink(self.dpath , self._hdf_path_base % self.arm_number)
