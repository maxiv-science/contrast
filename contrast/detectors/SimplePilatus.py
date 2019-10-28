"""
Provides a Pilatus interface based on a simple Tango device
developed at MAX IV. No LIMA. Temporary.
"""

from .Detector import Detector
from ..environment import env

import time
import numpy as np
try:
    import PyTango
except ModuleNotFoundError:
    pass

class SimplePilatus(Detector):

    def __init__(self, name=None, devname=None):
        """
        Lima is sometimes very slow to finish writing data, which is why this
        gadget has a 'hybrid mode', where Lima is started only once, and sequential
        arm/start calls to this gadget only increment counters. The busy state
        is set based on Lima's last_image_acquired compared to these counters,
        and does not reflect the state of the Lima device.
        """
        self.devname = devname
        Detector.__init__(self, name=name)

    def initialize(self):
        self.dev = PyTango.DeviceProxy(self.devname)
        self.dev.imgpath = '/lima_data'
        self.dev.nimages = 1

    def prepare(self, acqtime, dataid, n_starts):
        """
        Run before acquisition, once per scan. Set up triggering,
        number of images etc.
        """

        if self.busy():
            raise Exception('%s is busy!' % self.name)

        self.dev.exptime = acqtime

    def arm(self):
        """
        Start the detector if hardware triggered, just prepareAcq otherwise.
        """
        pass

    def start(self):
        """
        Start acquisition when software triggered.
        """

        if self.busy():
            raise Exception('%s is busy!' % self.name)
        self.dev.exposure('img')

    def stop(self):
        pass

    def busy(self):
        return self.dev.State() != PyTango.DevState.ON

    def read(self):
        return None

