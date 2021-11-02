"""
Provides a ``Motor`` subclass for Nanos positioners.
"""

import PyTango
from . import Motor

class NanosMotor(Motor):
    """
    Single Nanos motor axis.
    """

    def __init__(self, device, axis, **kwargs):
        """
        :param device: Path to the Bmc101 Tango device
        :type device: str
        :param axis: Axis number on the controller
        :type axis: int
        :param ``**kwargs``: Passed on to the ``Motor`` base class
        """
        super(NanosMotor, self).__init__(**kwargs)
        self.proxy = PyTango.DeviceProxy(device)
        self.proxy.set_source(PyTango.DevSource.DEV)
        self.proxy.Connect()
        self.axis = int(axis)

    @property
    def dial_position(self):
        return self.proxy.channel'%02.d'_position % (self.axis)

    @dial_position.setter
    def dial_position(self, pos):
        self.proxy.channel'%.2d'_position '%f' % (self.axis, pos)

    def busy(self):
        state = self.proxy.channel'%.2d'_state % (self.axis)
        # Nanos return this:
        # STATIONARY or MOVING
        return not (state == 'STATIONARY')

    def stop(self):
        self.proxy.StopAll() # safety first


