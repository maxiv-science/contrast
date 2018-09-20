from .Detector import Detector, LiveDetector

import time
import numpy as np

class Pilatus(Detector, LiveDetector):
    def __init__(self, name=None, lima_device=None, det_device=None):
        Detector.__init__(self, name=name)
        LiveDetector.__init__(self)
        self.lima = PyTango.DeviceProxy(lima_device)
        self.det = PyTango.DeviceProxy(det_device)
        
        self.lima.write_attribute('acq_trigger_mode', "INTERNAL_TRIGGER")
        self.lima.write_attribute('saving_mode', "MANUAL")
        self.lima.write_attribute('saving_frame_per_file', 1)
        self.lima.write_attribute('acq_nb_frames', 1)
        self.lima.write_attribute('saving_managed_mode', 'SOFTWARE')
        self.lima.write_attribute('saving_overwrite_policy', 'MULTISET')
        self.lima.set_timeout_millis(10000)
        self.lima.write_attribute('saving_format', 'HDF5')
        self.lima.write_attribute('saving_suffix', '.hdf5')
#        self.lima.write_attribute('saving_prefix',  ...
