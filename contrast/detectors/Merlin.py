from .Detector import Detector, SoftwareLiveDetector, TriggeredDetector, BurstDetector
from ..recorders.Hdf5Recorder import Link
from ..environment import env

import time
import numpy as np
import os
import requests
import json
import zmq
from threading import Thread

TRIG_MODES = {'internal': 0, 'rising_ttl': 1, 'soft': 5}

class Merlin(Detector, SoftwareLiveDetector, TriggeredDetector, BurstDetector):
    """
    Provides an interface to the Merlin detector streaming manager,

    https://github.com/maxiv-science/merlin-streamer
    """
    def __init__(self, name=None, host='b-nanomax-controlroom-cc-2', port=8000):
        self.host = host
        self.port = port
        self._hdf_path = 'entry/measurement/Merlin/data'
        self.acqthread = None
        self._gapless = False
        Detector.__init__(self, name=name)
        SoftwareLiveDetector.__init__(self)
        TriggeredDetector.__init__(self)
        BurstDetector.__init__(self)

    @property
    def gapless(self):
        """ Whether to use the continuous alternating-counter mode """
        return self._gapless

    @gapless.setter
    def gapless(self, val):
        self._gapless = bool(val)

    def initialize(self):
        self.session = requests.Session()
        self.session.trust_env = False

        self.session = requests.Session()
        self.session.trust_env = False
        self.burst_latency = 1.64e-3

    def get(self, key):
        response = self.session.get('http://%s:%d/%s' %(self.host, self.port, key))
        if response:
            return response.json()['value']
        else:
            print('error', response)

    def set(self, key, value=None):
        url = 'http://%s:%d/%s' %(self.host, self.port, key)
        if value is None:
            payload = None
        else:
            payload = {'value': value}
        response = self.session.put(url, json=payload)
        if response.status_code != 200:
            print(response.text)
            return False
        else:
            return True

    def busy(self):
        if self.acqthread and self.acqthread.is_alive():
            return True
        else:
            return False

    @property
    def energy(self):
        """ Operating photon energy """
        return self.get('energy')

    @energy.setter
    def energy(self, val):
        if (val < 4) or (val > 30):
            print('Bad energy value, should be in keV and between 4-30')
            return
        val = float(val)
        self.set('energy', val)

    def prepare(self, acqtime, dataid, n_starts):
        BurstDetector.prepare(self, acqtime, dataid, n_starts)
        if n_starts is None:
            n_starts = 10000
        self.set('num_frames_per_trigger', self.burst_n)
        self.set('acquisition_time', self.acqtime * 1000)
        self.set('acquisition_period', (self.acqtime + self.burst_latency) * 1000)
        self.set('counterdepth', 24)
        if self.gapless:
            if self.hw_trig:
                assert (self.hw_trig_n == 1), 'Only hw_trig_n=1 is allowed for gapless operation'
                self.set('trigger_start', TRIG_MODES['rising_ttl'])
            else:
                self.set('trigger_start', TRIG_MODES['internal'])
            self.set('num_frames', int(self.burst_n))
            self.set('continuousrw', True)
            
        elif self.hw_trig:
            self.set('trigger_start', TRIG_MODES['rising_ttl'])
            self.set('num_frames', int(self.burst_n * self.hw_trig_n * n_starts))
        else:
            self.set('trigger_start', TRIG_MODES['soft'])
            self.set('num_frames', int(n_starts * self.burst_n)) # np.int64 isn't json serializable
        if dataid is None:
            self.dpath = ''
        else:
            filename = 'scan_%06d_%s.hdf5' % (dataid, self.name)
            self.dpath = os.path.join(env.paths.directory, filename)
            if os.path.exists(self.dpath):
                print('%s: this hdf5 file exists, I am raising an error now'%self.name)
                raise Exception('%s hdf5 file already exists' % self.name)
        self.set('filename', self.dpath)
        if not self.gapless:
            self.set('arm')

    def arm(self):
        # The Merlin is armed only once.
        if not self.hw_trig:
            return

        if self.gapless:
            nframes = self.burst_n
            self.set('arm') # this actually starts the detector
            time.sleep(.1)
        else:
            nframes = self.hw_trig_n * self.burst_n
        self.acqthread = Thread(target=self.set, args=('start', nframes))
        self.acqthread.start()

    def start(self):
        if self.hw_trig:
            return
        # how many frames will this particular start() call cause?
        if self.gapless:
            nframes = self.burst_n
            self.set('arm') # this actually starts the detector
        else:
            nframes = self.burst_n
        # the following command will issue a soft trigger if applicable,
        # otherwise just sets up the data acquisition on the REST server.
        self.acqthread = Thread(target=self.set, args=('start', nframes))
        self.acqthread.start()

    def stop(self):
        self.set('stop')

    def read(self):
        if self.dpath:
            ret = {'frames': Link(self.dpath , self._hdf_path, universal=True),
                   'thumbs:': None,}
        else:
            ret = None
        return ret

    def _start(self, acqtime):
        """
        The Merlin also needs to override this method as it uses software triggers.
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

