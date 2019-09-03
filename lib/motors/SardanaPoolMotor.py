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

    def __init__(self, device, **kwargs):
        super(SardanaPoolMotor, self).__init__(**kwargs)
        self.proxy = PyTango.DeviceProxy(device)

    @dial_position.setter
    def dial_position(self, pos):
        self.proxy.Position = pos

    @property
    def dial_position(self):
        return self.proxy.Position

    def busy(self):
        state = self.proxy.State()
        return not (state == PyTango.DevState.ON)

    def stop(self):
        self.proxy.stop()
