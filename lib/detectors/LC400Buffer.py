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

    def __init__(self, name=None, device=None, xaxis=2, yaxis=3, zaxis=1):
        self.proxy = PyTango.DeviceProxy(device)
        Detector.__init__(self, name=name)
        self.xaxis = xaxis
        self.yaxis = yaxis
        self.zaxis = zaxis

    def initialize(self):
        self.proxy.init()

    def stop(self):
        self.proxy.Stop()

    def busy(self):
        return not (self.proxy.State() in (PyTango.DevState.STANDBY, PyTango.DevState.ON))

    def read(self):
        self.proxy.ReadLC400Buffer()
        data = {1: self.proxy.Axis1Positions,
                2: self.proxy.Axis2Positions,
                3: self.proxy.Axis3Positions,}
        return {'x': data[self.xaxis], 'y': data[self.yaxis], 'z': data[self.zaxis]}

    def start(self):
        """
        Placeholder, this detector just reads out whatever buffer is on the
        scancontrol device. That device is managed manually from macros.
        """
        pass

