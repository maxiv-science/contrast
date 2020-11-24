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
        self.proxy.set_source(PyTango.DevSource.DEV)

    @property
    def dial_position(self):
        return self.proxy.Position

    @dial_position.setter
    def dial_position(self, pos):
        self.proxy.Position = pos

    @property
    def dial_limits(self):
        """
        Overridden to expose the limits on the Pool motor.
        """
        _min = float(self.proxy.get_attribute_config("position").min_value)
        _max = float(self.proxy.get_attribute_config("position").max_value)
        return _min, _max

    @dial_limits.setter
    def dial_limits(self, lims):
        config = self.proxy.get_attribute_config("position")
        config.min_value = str(lims[0])
        config.max_value = str(lims[1])
        self.proxy.set_attribute_config(config)

    def busy(self):
        state = self.proxy.State()
        if state == PyTango.DevState.ON:
            return False
        elif state == PyTango.DevState.ALARM:
            lim1 = self.proxy.read_attribute('StatusLim-').value
            lim2 = self.proxy.read_attribute('StatusLim+').value
            if lim1 or lim2:
                # probably just a limit switch, then
                return False
        return True

    def stop(self):
        self.proxy.stop()

