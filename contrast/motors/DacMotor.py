"""
Provides a ``Motor`` subclass for piezo controllers commanded by a National Instruments DAC output device.
"""

import PyTango
import time
import math
from . import Motor


class DacMotor(Motor):
    """
    Single DAC controlled piezo axis.
    """

    def __init__(self, device, axis, **kwargs):
        """
        :param device: Path to the DAC WaveForm Tango device
        :type device: str
        :param axis: Axis number on the controller
        :type axis: int
        :param ``**kwargs``: Passed on to the ``Motor`` base class
        """
        super(DacMotor, self).__init__(**kwargs)
        self.proxy = PyTango.DeviceProxy(device)
        self.proxy.set_source(PyTango.DevSource.DEV)
        self._axis = int(axis)

    @property
    def dial_position(self):
        attr = 'dac_%d_position' % self._axis
        return self.proxy.read_attribute(attr).value

    @dial_position.setter
    def dial_position(self, pos):
        attr = 'dac_%d_position' % self._axis
        self.proxy.write_attribute(attr, pos)

    def busy(self):
        return self.proxy.read_attribute('dac_%d_is_moving' % self._axis).value
 



