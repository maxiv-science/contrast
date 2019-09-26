"""
Provides a Motor interface to Tango motors.
"""

import PyTango
from . import Motor

class TangoMotor(Motor):
    """
    Single motor as exposed by Pool. Use for IcePAP:s.
    """

    def __init__(self, device, **kwargs):
        super(TangoMotor, self).__init__(**kwargs)
        self.proxy = PyTango.DeviceProxy(device)

    @property
    def dial_position(self):
        return self.proxy.Position

    @dial_position.setter
    def dial_position(self, pos):
        self.proxy.Position = pos

    def busy(self):
        state = self.proxy.State()
        return not (state == PyTango.DevState.ON)

    def stop(self):
        self.proxy.stop()

