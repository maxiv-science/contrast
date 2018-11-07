"""
Provides a Motor interface to the motor Tango devices exposed
by Sardana's Pool. This is a temporary configuration since
IcePAP:s for example do not have proper Tango servers.
"""

import PyTango
from . import Motor

class SardanaPoolMotor(Motor):
    """
    Single motor as exposed by Pool. Use for IcePAP:s.
    """

    def __init__(self, name, device):
        super(SardanaPoolMotor, self).__init__(name=name)
        self.proxy = PyTango.DeviceProxy(device)

    def move(self, pos):
        if super(SardanaPoolMotor, self).move(pos) == 0:
            self.proxy.Position = pos

    def position(self):
        return self.proxy.Position

    def busy(self):
        state = self.proxy.State()
        return not (state == PyTango.DevState.ON)

    def stop(self):
        self.proxy.stop()

