from .Detector import Detector, TriggeredDetector
from ..recorders.Hdf5Recorder import Link
from ..environment import env

import time
import numpy as np
import os
try:
    import tango
except ImportError:
    pass


class QEPro6500(Detector, TriggeredDetector):
    """
    Provides a direct interface to the Ocenview QEPro 6500 spectroemter via a Tango Server.
    """

    def __init__(self, device, name=None,
                 hdf_path='entry/instrument/QEPro/data',
                 hw_trig_min_latency=0.01,
                 trigger_mode=3,
                 nonlinearity_correction=True,
                 electric_dark_correction=True,
                 ):
        self.proxy = tango.DeviceProxy(device)
        self.proxy.set_timeout_millis(10000)
        # self.acqthread = None
        self._hdf_path = hdf_path
        self.name = name
        self.hw_trig_min_latency = hw_trig_min_latency
        self.trigger_mode = trigger_mode
        self.nonlinearity_correction = nonlinearity_correction
        self.electric_dark_correction = electric_dark_correction
        Detector.__init__(self, name=name)
        TriggeredDetector.__init__(self)

    def initialize(self):
        self.n_started = 0
        print(f"{self.name}: Initilazing the Tango Server...", end="")
        self.proxy.Init()
        # set explicitly to hardware trigger mode
        self.proxy.TriggerMode = self.trigger_mode
        self.proxy.nonlinearity_correction = self.nonlinearity_correction
        self.proxy.electric_dark_correction = self.electric_dark_correction
        print(f" done.")

    def busy(self):
        # if self.proxy.State() == tango.DevState.RUNNING:
        #     return True
        # else:
        #     return False
        # We cannot rely purly on the nFramesReceived attribute, as it is not reset at the end of an acquisition
        # so we check the State first, to see if it is idle
        if self.proxy.State() == tango.DevState.ON:
            return False
        if self.proxy.nFramesReceived < self.n_started:
            return True
        else:
            return False

    @property
    def temperature(self):
        """ Actual sensor temperature of the spectrometer"""
        return self.proxy.Temperature

    @property
    def temperature_setpoint(self):
        """ Temperature setpoint of the sensor """
        return self.proxy.TemperatureSetpoint

    @temperature_setpoint.setter
    def temperature_setpoint(self, val):
        self.proxy.TemperatureSetpoint = float(val)


    def prepare(self, acqtime, dataid, n_starts):
        print(f"calling prepare() with {acqtime = }, {dataid = }, {n_starts = }")
        print(f"{acqtime = }, {self.hw_trig_n = }, {dataid = }")
        self.dpath = ''
        if self.busy():
            raise Exception(f'{self.name} is busy!')
        
        self.repetitions = self.hw_trig_n if self.hw_trig else 1
        
        self.proxy.ExposureTime = acqtime
        self.proxy.nTriggers = self.hw_trig_n
        self.proxy.DestinationFileName = f"{dataid}"
        self.proxy.Prepare()
            
        # if (dataid is None) or (env.paths.directory is None):
        #     self.dpath = ''
        # else:
        #     path = env.paths.directory
        #     filename = 'scan_%06d_%s.h5' % (dataid, self.name)
        #     self.dpath = os.path.join(env.paths.directory, filename)
        #     if os.path.exists(self.dpath):
        #         print('%s: this hdf5 file exists, I am raising an error now'
        #               % self.name)
        #         raise Exception('%s hdf5 file already exists' % self.name)
        # self.proxy.DestinationFilename = self.dpath
        # if self.hw_trig:
        #     self.proxy.TriggerMode = 'EXTERNAL_MULTI'
        #     self.proxy.nTriggers = self.hw_trig_n * n_starts
            
        # else:
        #     self.proxy.TriggerMode = 'INTERNAL'
        #     self.proxy.nTriggers = n_starts
        #     self.proxy.nFramesPerTrigger = self.burst_n
            
        # self.proxy.Arm()
        self.n_started = 0

    def arm(self):
        print("calling arm()")

    def start(self):
        print("calling start()")
        # self.n_started += self.repetitions
        # if not self.hw_trig:
        #     self.proxy.Trigger()

    def stop(self):
        print("calling stop()")
        self.proxy.Stop()
        self.n_started = 0

    def read(self):
        print("calling read()")
        if self.dpath:
            ret = {'frames': Link(self.dpath, self._hdf_path, universal=True)}
        else:
            ret = None
        return ret
