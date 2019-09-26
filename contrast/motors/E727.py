"""
Provides a Motor subclass for the PI E727 piezo driver.
"""

import PyTango
from . import Motor

class E727Motor(Motor):
    """
    Single axis on the E727.
    """

    def __init__(self, device, axis, **kwargs):
        super(E727Motor, self).__init__(**kwargs)
        assert axis in (1, 2, 3)
        self.proxy = PyTango.DeviceProxy(device)
        self.axis = axis
        if axis == 1:
            self._mvrelfunc = self.proxy.move_relative1
        elif axis == 2:
            self._mvrelfunc = self.proxy.move_relative2
        elif axis == 3:
            self._mvrelfunc = self.proxy.move_relative3

    def _server_position(self):
        if self.axis == 1:
            return self.proxy.position1
        elif self.axis == 2:
            return self.proxy.position2
        elif self.axis == 3:
            return self.proxy.position3

    @property
    def dial_position(self):
        return = self._server_position()

    @dial_position.setter
    def dial_position(self, pos):
        current = self._server_position()
        self._mvrelfunc(pos - current)

    def busy(self):
        state = self.proxy.State()
        if state in (PyTango.DevState.STANDBY, PyTango.DevState.ON):
            return False
        return True

    def stop(self):
        self.proxy.stop()
