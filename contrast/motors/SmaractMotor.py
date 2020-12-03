"""
Provides a ``Motor`` subclass for Smaract positioners.
"""

import PyTango
from . import Motor

class SmaractLinearMotor(Motor):
    """
    Single Smaract motor axis.
    """

    def __init__(self, device, axis, **kwargs):
        """
        :param device: Path to the MCS Tango device
        :type device: str
        :param axis: Axis number on the controller
        :type axis: int
        :param ``**kwargs``: Passed on to the ``Motor`` base class
        """
        super(SmaractLinearMotor, self).__init__(**kwargs)
        self.proxy = PyTango.DeviceProxy(device)
        self.proxy.set_source(PyTango.DevSource.DEV)
        self.axis = int(axis)

    @property
    def dial_position(self):
        return self.proxy.Read_position(self.axis)

    @dial_position.setter
    def dial_position(self, pos):
        self.proxy.Write_position('%d, %f' % (self.axis, pos))

    def busy(self):
        state = self.proxy.channel_status(self.axis)
        # Smaracts return this:
        # 0 (ON), 1 (MOVING), 2 (ALARM)
        return not (state == 0)

    def stop(self):
        self.proxy.stop_all() # safety first

class SmaractRotationMotor(SmaractLinearMotor):
    @property
    def dial_position(self):
        result = eval(self.proxy.Arbitrary_command('GA%u'%self.axis))
        pos = int(result[2])
        rev = int(result[3])
        sign = 1 if (rev == 0) else 1
        if rev == 0:
            pos = pos * 1e-6
        else:
            pos = pos * 1e-6 - 360
        return pos

    @dial_position.setter
    def dial_position(self, pos):
        if pos < 0:
            rev = -1
            pos = (pos + 360) * 1e6
        else:
            rev = 0
            pos = pos * 1e6
        self.proxy.Write_angle('%d, %u, %u' % (self.axis, int(pos), rev))

