from .Detector import Detector, LiveDetector, TriggeredDetector, Link
from ..environment import env

import time
import numpy as np
import PyTango

class Pilatus(Detector, LiveDetector, TriggeredDetector):
    def __init__(self, name=None, lima_device=None, det_device=None):
        Detector.__init__(self, name=name)
        LiveDetector.__init__(self)
        TriggeredDetector.__init__(self)
        self.lima_device_name = lima_device
        self.det_device_name = det_device

    def initialize(self):
        self.lima = PyTango.DeviceProxy(self.lima_device_name)
        self.lima.set_timeout_millis(10000)
        self.det = PyTango.DeviceProxy(self.det_device_name)
        
        self.lima.acq_trigger_mode = "INTERNAL_TRIGGER"
        self.lima.saving_mode = "AUTO_FRAME"
        self.lima.saving_frame_per_file = 1
        self.lima.acq_nb_frames = 1
        self.lima.saving_managed_mode = 'SOFTWARE'
        self.lima.saving_overwrite_policy = 'MULTISET'
        self.lima.saving_format = 'HDF5'
        self.lima.saving_suffix = '.hdf5'
        self.lima.saving_directory = '/scan_data/temp/'

    def prepare(self, acqtime, dataid):
        """
        Run before acquisition, once per scan. Set up triggering,
        number of images etc.
        """
        # get out of the fault caused by trigger timeout
        if (self.lima.acq_status == 'Fault') and (self.lima.acq_status_fault_error == 'No error'):
            self.lima.stopAcq()
            self.lima.prepareAcq()

        if self.busy():
            raise Exception('%s is busy!' % self.name)

        if dataid is None:
            # no saving
            self.lima.saving_mode = "MANUAL" # no saving
            self.link = None
        else:
            # saving
            self.lima.saving_directory = env.paths.directory
            self.lima.saving_mode = "AUTO_FRAME"
            filename = 'scan_%04d_%s' % (dataid, self.name)
            self.lima.saving_prefix = filename
            self.link = Link(filename + self.lima.saving_suffix)

        if self.hw_trig:
            self.lima.acq_trigger_mode = "EXTERNAL_TRIGGER_MULTI"
            self.lima.acq_nb_frames = self.hw_trig_n
        else:
            self.lima.acq_trigger_mode = "INTERNAL_TRIGGER"
            self.lima.acq_nb_frames = 1

        self.acqtime = acqtime
        self.lima.acq_expo_time = acqtime

    def arm(self):
        """
        Start the detector if hardware triggered, just prepareAcq otherwise.
        """
        if self.busy():
            raise Exception('%s is busy!' % self.name)
        self.lima.prepareAcq()
        if self.hw_trig:
            self.lima.startAcq()

    def start(self):
        """
        Start acquisition when software triggered.
        """
        if self.busy():
            raise Exception('%s is busy!' % self.name)
        if not self.hw_trig:
            self.lima.startAcq()

    def stop(self):
        self.lima.stopAcq()

    def busy(self):
        return not self.lima.ready_for_next_acq

    def read(self):
        return self.link
