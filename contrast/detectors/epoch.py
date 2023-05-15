from .Detector import Detector, SoftwareLiveDetector, TriggerSource

import time
import numpy as np
import h5py
from ..recorders.Hdf5Recorder import Link


class Epoch(Detector, SoftwareLiveDetector):
    """
    Detector which returns the unix time in GMT 0 time zone.
    """
    def __init__(self, name=None):
        Detector.__init__(self, name=name)
        SoftwareLiveDetector.__init__(self)

    def initialize(self):
        pass

    def start(self):
        super(Epoch, self).start()
        try:
            self.val = time.time()
            self._started = time.time()
        except AttributeError:
            raise Exception('Detector not prepared!')

    def stop(self):
        try:
            self._started = time.time() - self.acqtime
        except AttributeError:
            return

    def busy(self):
        try:
            return time.time() < self._started + self.acqtime
        except AttributeError:
            return False

    def read(self):
        try:
            return self.val
        except AttributeError:
            raise Exception('Detector not started!')
