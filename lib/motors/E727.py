"""
Provides a Motor subclass for the PI E727 piezo driver.
"""

import PyTango
from . import Motor

class E727Motor(Motor):
    """
    Single axis on the E727.

    Optionally, you can supply offset and scale numbers.
    The user position is then calculated from the PI
    server positions as
        p_user = p_pi * scale + offset
    and obviously vice versa when calculating new PI server
    values.
    """

    def __init__(self, name, device, axis, offset=0, scale=1):
        super(E727Motor, self).__init__(name=name)
        assert axis in (1, 2, 3)
        self.proxy = PyTango.DeviceProxy(device)
        self.axis = axis
        if axis == 1:
            self._mvrelfunc = self.proxy.move_relative1
        elif axis == 2:
            self._mvrelfunc = self.proxy.move_relative2
        elif axis == 3:
            self._mvrelfunc = self.proxy.move_relative3
        self.offset = offset
        self.scale = scale

    def _server_position(self):
        if self.axis == 1:
            return self.proxy.position1
        elif self.axis == 2:
            return self.proxy.position2
        elif self.axis == 3:
            return self.proxy.position3

    def move(self, pos):
        if super(E727Motor, self).move(pos) == 0:
            current_dial = self._server_position()
            new_dial = (pos - self.offset) / self.scale
            self._mvrelfunc(new_dial - current_dial)

    def position(self):
        dial = self._server_position()
        user = dial * self.scale + self.offset
        return user

    def busy(self):
        state = self.proxy.State()
        if state in (PyTango.DevState.STANDBY, PyTango.DevState.ON):
            return False
        return True

    def stop(self):
        self.proxy.stop()

