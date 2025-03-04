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



class SelunTangoFG(Detector, SoftwareLiveDetector, TriggeredDetector, BurstDetector):
    """
    Provides a direct interface to the Dectris SELUN server via a Tango Server that uses the file grabber.
    """

    def __init__(self, device_name, name=None,
                 #api_version='1.8.0', use_image_appendix=False,
                 hdf_path='entry/data/data_000001',
                 hw_trig_min_latency=100e-9):
        """
        Class to interact directly with the SELUN tango device based on the FG.
        """
        self.proxy = tango.DeviceProxy(device_name)
        self.proxy.set_timeout_millis(10000)
        self.acqthread = None
        self._hdf_path = hdf_path
        self.name = name
        self.hw_trig_min_latency = hw_trig_min_latency
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
    
    def busy(self):
        # if self.proxy.State() == tango.DevState.RUNNING:
        #     return True
        # else:
        #     return False
        # We cannot rely purly on the nFramesReceived attribute, as it is not reset at the end of an acquisition
        # so we check the State first, to see if it is idle
        if self.proxy.State() == tango.DevState.STANDBY:
            return False
        #if self.proxy.nFramesReceived < self.n_started*self.burst_n:
        #    return True
        else:
            return False

    @property
    def energy(self):
        """ Operating energy in eV """
        return self.proxy.PhotonEnergy

    @energy.setter
    def energy(self, val):
        if (val < 10000) or (val > 80000):
            print('Bad energy value, should be in between 10 000 eV and 80 000 eV')
            return
        val = float(val)
        self.proxy.PhotonEnergy = val
        print(f'energy of {self.name} has been set to {self.energy} eV')

    @property
    def mask_applied(self):
        """ Whether to apply the mask """
        return self.proxy.PixelMaskApplied

    @mask_applied.setter
    def mask_applied(self, val):
        self.proxy.PixelMaskApplied = val

    @property
    def threshold(self):
        """ Energy threshold for the counters """
        return self.proxy.EnergyThreshold

    @threshold.setter
    def threshold(self, val):
        self.proxy.EnergyThreshold = val

    @property
    def imagesperfile(self):
        """ Energy threshold for the counters """
        return self.proxy.ImagesPerFile

    @imagesperfile.setter
    def threshold(self, val):
        self.proxy.ImagesPerFile = val

    def prepare(self, acqtime, dataid, n_starts):

        try:
            BurstDetector.prepare(self, acqtime, dataid, n_starts)
            acqtime = self.acqtime
            
            if self.busy():
                raise Exception(f'{self.name} is busy!')
            
            self.proxy.NbImages = self.burst_n    
            self.proxy.CountTime = acqtime  
            self.proxy.FrameTime = acqtime + self.burst_latency
            #self.proxy.ExposureTime = acqtime
            self.repetitions = self.hw_trig_n if self.hw_trig else 1        
                
            if (dataid is None) or (env.paths.directory is None):
                self.dpath = ''
            else:
                path = env.paths.directory
                filename = 'scan_%06d_%s_master.h5' % (dataid, self.name)
                self.dpath = os.path.join(env.paths.directory, filename)
                if os.path.exists(self.dpath):
                    print('%s: this hdf5 file exists, I am raising an error now'
                          % self.name)
                    raise Exception('%s hdf5 file already exists' % self.name)
            
            self.proxy.FilenamePattern = self.dpath.replace('_master.h5', '')
            if self.hw_trig:
                self.proxy.TriggerMode = 'exts'
                self.proxy.NbImages = self.burst_n
                self.proxy.NbTriggers = self.hw_trig_n * n_starts

                # exts ... external trigger series
                # Nimages ... per trigger
                # Ntrigger ... number of triggers
                
            else:
                self.proxy.TriggerMode = 'ints'
                self.proxy.ImagesPerFile = n_starts * self.burst_n
                self.proxy.NbTriggers = n_starts
                self.proxy.NbImages = self.burst_n
                
            self.proxy.Arm()
            self.n_started = 0
        except Exception as E:
            print(E)

    def arm(self):
        # The Selun is armed only once.
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
        
