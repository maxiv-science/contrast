"""
Provides a Motor subclass for the Npoint LC400 piezo driver.
"""

import PyTango
from . import Motor

class LC400Motor(Motor):
    """
    Single axis on the LC400.

    Optionally, you can supply offset and scale numbers.
    The user position is then calculated from the npoint
    server positions as
        p_user = p_npoint * scale + offset
    and obviously vice versa when calculating new Npoint server
    values.
    """

    def __init__(self, device, axis, offset=0, scale=1, **kwargs):
        super(LC400Motor, self).__init__(**kwargs)
        assert axis in (1, 2, 3)
        self.proxy = PyTango.DeviceProxy(device)
        self.axis = axis
        self.offset = offset
        self.scale = scale
        self._format = '%.3f'

    def _get_dial_pos(self):
        if self.axis == 1:
            val = self.proxy.axis1_position
        elif self.axis == 2:
            val = self.proxy.axis2_position
        elif self.axis == 3:
            val = self.proxy.axis3_position
        return val

    def _set_dial_pos(self, pos):
        if self.axis == 1:
            self.proxy.axis1_position = pos
        elif self.axis == 2:
            self.proxy.axis2_position = pos
        elif self.axis == 3:
            self.proxy.axis3_position = pos

    def move(self, pos):
        if super(LC400Motor, self).move(pos) == 0:
            new_dial = (pos - self.offset) / self.scale
            self._set_dial_pos(new_dial)

    def position(self):
        dial = self._get_dial_pos()
        user = dial * self.scale + self.offset
        return user

    def busy(self):
        state = self.proxy.State()
        if state in (PyTango.DevState.STANDBY, PyTango.DevState.ON):
            return False
        return True

    def stop(self):
        self.proxy.stop_waveform()
        self.proxy.stop_recording()

