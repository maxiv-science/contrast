"""
Provides a general Motor interface to any Tango attribute.
"""

import PyTango
from . import Motor

class TangoAttributeMotor(Motor):
    """
    Motor interface to any Tango attribute, so that anything can be
    scanned. These motors cannot be stopped and are never considered
    busy.
    """

    def __init__(self, device, attribute, force_read=True, **kwargs):
        """
        :param device: Path to the Tango device
        :type device: str
        :param attribute: Name of the Tango attribute
        :type attribute: str
        :param ``**kwargs``: Passed to the ``Motor`` base class
        """
        super(TangoAttributeMotor, self).__init__(**kwargs)
        self.proxy = PyTango.DeviceProxy(device)
        if force_read:
            self.proxy.set_source(PyTango.DevSource.DEV)
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
