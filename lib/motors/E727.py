"""
Provides a Motor subclass for the PI E727 piezo driver.
"""

import PyTango
from . import Motor

class E727Motor(Motor):
    """
    Single axis on the E727.
    """

    def __init__(self, tango_device='B303A-EH/CTL/PZCU-02', axis=None, name=None):
        super(E727Motor, self).__init__(name=name)

        assert axis in (1, 2, 3)
        self.proxy = PyTango.DeviceProxy(tango_device)
        self.axis = axis
        if axis == 1:
            self._mvrelfunc = self.proxy.move_relative1
        elif axis == 2:
            self._mvrelfunc = self.proxy.move_relative2
        elif axis == 3:
            self._mvrelfunc = self.proxy.move_relative3

    def move(self, pos):
        if super(E727Motor, self).move(pos) == 0:
            current = self.position()
            rel = pos - current
            self._mvrelfunc(rel)

    def position(self):
        if self.axis == 1:
            return self.proxy.position1
        elif self.axis == 2:
            return self.proxy.position2
        elif self.axis == 3:
            return self.proxy.position3

    def busy(self):
        state = self.proxy.State()
        if state in (PyTango.DevState.STANDBY, PyTango.DevState.ON):
            return False
        return True

    def stop(self):
        self.proxy.stop()

