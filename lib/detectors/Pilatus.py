from .Detector import Detector, LiveDetector, Link

import time
import numpy as np
import PyTango

class Pilatus(Detector, LiveDetector):
    def __init__(self, name=None, lima_device=None, det_device=None):
        Detector.__init__(self, name=name)
        LiveDetector.__init__(self)

        self.name = name
        self.link = None

        self.lima = PyTango.DeviceProxy(lima_device)
        self.lima.set_timeout_millis(10000)
        self.det = PyTango.DeviceProxy(det_device)
        
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
        if self.busy():
            raise Exception('%s is busy!' % self.name)

        filename = 'scan_%04d_%s_' % (dataid, self.name)
            
        self.acqtime = acqtime
        self.lima.acq_expo_time = acqtime
        self.lima.saving_prefix = filename
        self.link = Link(filename)

    def arm(self):
        """
        Start the detector if hardware triggered, just prepareAcq otherwise.
        """
        if self.busy():
            raise Exception('%s is busy!' % self.name)
        self.lima.prepareAcq()

    def start(self):
        """
        Start acquisition when software triggered.
        """
        if self.busy():
            raise Exception('%s is busy!' % self.name)
        self.lima.startAcq()

    def stop(self):
        self.lima.stopAcq()

    def busy(self):
        return not self.lima.ready_for_next_acq

    def read(self):
        return self.link

