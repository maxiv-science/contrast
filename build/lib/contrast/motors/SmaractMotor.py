"""
Provides a Motor subclass for Smaracts.
"""

import PyTango
from . import Motor

class SmaractLinearMotor(Motor):
    """
    Single Smaract motor axis.
    """

    def __init__(self, device, axis, **kwargs):
        super(SmaractLinearMotor, self).__init__(**kwargs)
        self.proxy = PyTango.DeviceProxy(device)
        self.axis = int(axis)

    @property
    def dial_position(self):
        return self.proxy.Read_position(self.axis)

    @dial_position.setter
    def dial_position(self, pos):
        self.proxy.Write_position('%d, %f' % (self.axis, pos))

    def busy(self):
        state = self.proxy.channel_status(self.axis)
        # Smaracts return this:
        # 0 (ON), 1 (MOVING), 2 (ALARM)
        return not (state == 0)

    def stop(self):
        self.proxy.stop_all() # safety first
