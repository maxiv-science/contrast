"""
Provides a Motor subclass for Smaracts.
"""

import PyTango
from . import Motor

class SmaractLinearMotor(Motor):
    """
    Single Smaract motor axis.

    Optionally, you can supply offset and scale numbers.
    The user position is then calculated from the Smaract
    server positions as
        p_user = p_smaract * scale + offset
    and obviously vice versa when calculating new Smaract
    values.
    """

    def __init__(self, name, device, axis, offset=0, scale=1):
        super(SmaractLinearMotor, self).__init__(name=name)
        self.proxy = PyTango.DeviceProxy(device)
        self.axis = int(axis)
        self.offset = offset
        self.scale = scale

    def move(self, pos):
        if super(SmaractLinearMotor, self).move(pos) == 0:
            dial = (pos - self.offset) / self.scale
            self.proxy.Write_position('%d, %f' % (self.axis, dial))

    def position(self):
        dial = self.proxy.Read_position(self.axis)
        user = dial * self.scale + self.offset
        return user

    def busy(self):
        state = self.proxy.channel_status(self.axis)
        # Smaracts return this:
        # 0 (ON), 1 (MOVING), 2 (ALARM)
        return not (state == 0)

    def stop(self):
        self.proxy.stop_all() # safety first

