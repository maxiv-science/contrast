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

    def __init__(self, name, device, attribute):
        super(TangoAttributeMotor, self).__init__(name=name)
        self.proxy = PyTango.DeviceProxy(device)
        self.attribute = attribute

    def move(self, pos):
        if super(TangoAttributeMotor, self).move(pos) == 0:
            self.proxy.write_attribute(self.attribute, pos)

    def position(self):
        return self.proxy.read_attribute(self.attribute).value

    def busy(self):
        return False

    def stop(self):
        pass

