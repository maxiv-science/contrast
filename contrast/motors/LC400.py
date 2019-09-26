"""
Provides a Motor subclass for the Npoint LC400 piezo driver.
"""

import PyTango
from . import Motor

class LC400Motor(Motor):
    """
    Single axis on the LC400.
    """

    def __init__(self, device, axis, **kwargs):
        super(LC400Motor, self).__init__(**kwargs)
        assert axis in (1, 2, 3)
        self.proxy = PyTango.DeviceProxy(device)
        self.axis = axis
        self._format = '%.3f'

    @property
    def dial_position(self):
        if self.axis == 1:
            val = self.proxy.axis1_position
        elif self.axis == 2:
            val = self.proxy.axis2_position
        elif self.axis == 3:
            val = self.proxy.axis3_position
        return val

    @dial_position.setter
    def dial_position(self, pos):
        if self.axis == 1:
            self.proxy.axis1_position = pos
        elif self.axis == 2:
            self.proxy.axis2_position = pos
        elif self.axis == 3:
            self.proxy.axis3_position = pos

    def busy(self):
        attribute = 'axis%d_position_on_target' % self.axis
        on_target = self.proxy.read_attribute(attribute).value
        return not on_target

    def stop(self):
        self.proxy.stop_waveform()
        self.proxy.stop_recording()
