"""
Provides a general Motor interface to any Tango attribute.
"""

import PyTango
from . import Motor

class TangoAttributeMotor(Motor):
    """
    Motor interface to any Tango attribute, so that anything can
    be scanned. These motors cannot be stopped and are never
    considered busy.
    """

    def __init__(self, device, attribute, **kwargs):
        super(TangoAttributeMotor, self).__init__(**kwargs)
        self.proxy = PyTango.DeviceProxy(device)
        self.attribute = attribute

    @property
    def dial_position(self):
        return self.proxy.read_attribute(self.attribute).value

    @dial_position.setter
    def dial_position(self, pos):
        self.proxy.write_attribute(self.attribute, pos)

    def busy(self):
        return False

    def stop(self):
        pass
