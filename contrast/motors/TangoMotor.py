"""
Provides a Motor interface to standard Tango motors.
"""

import PyTango
from . import Motor

class TangoMotor(Motor):
    """
    Single Tango motor.
    """

    def __init__(self, device, **kwargs):
        """
        :param device: Path to the Tango device
        :type device: str
        :param ``**kwargs``: Passed to the ``Motor`` base class
        """
        super(TangoMotor, self).__init__(**kwargs)
        self.proxy = PyTango.DeviceProxy(device)

    @property
    def dial_position(self):
        return self.proxy.Position

    @dial_position.setter
    def dial_position(self, pos):
        self.proxy.Position = pos

    def busy(self):
        state = self.proxy.State()
        acceptable = (PyTango.DevState.ON, PyTango.DevState.ALARM)
        return not (state in acceptable)

    def stop(self):
        self.proxy.stop()

