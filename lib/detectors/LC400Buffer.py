from .Detector import Detector

import time
import numpy as np
import PyTango

class LC400Buffer(Detector):
    """
    Class representing the LC400 piezo machine under the
    control of the LC400ScanControl Tango device, used for
    reading the flyscan positions.
    """

    def __init__(self, name=None, device=None):
        self.proxy = PyTango.DeviceProxy(device)
        Detector.__init__(self, name=name)

    def initialize(self):
        pass

    def stop(self):
        self.proxy.Stop()

    def busy(self):
        return not (self.proxy.State() in (PyTango.DevState.STANDBY, PyTango.DevState.ON))

    def read(self):
        self.proxy.ReadLC400Buffer()
        ax1 = self.proxy.Axis1Positions
        ax2 = self.proxy.Axis2Positions
        ax3 = self.proxy.Axis3Positions
        return np.stack((ax1, ax2, ax3), axis=1)

    def start(self):
        """
        Placeholder, this detector just reads out whatever buffer is on the
        scancontrol device. That device is managed manually from macros.
        """
        pass
