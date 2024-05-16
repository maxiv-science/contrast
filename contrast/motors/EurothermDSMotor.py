"""
Provides a ``Motor`` subclass for the EurothermDS tango device to change the 
temperature setpoint

for 20231270 Carbone (starting 2024/05/21)
"""

try:
    import tango
except ImportError:
    pass
from . import Motor
import time


class EuroThermDSMotor(Motor):
    """
    Single EuroThermDSM temperature motor axis for setting the temperature setpoint.
    Will only set 'Target setpoint loop1'.
    """
    def __init__(self, device, scaling_factor=10., **kwargs):
        """
        :param device: Path to the MCS Tango device
        :type device: str
        """
        super().__init__(**kwargs)
        self.proxy = tango.DeviceProxy(device)
        #self.proxy.set_source(tango.DevSource.DEV)
        self.scaling_factor = float(scaling_factor)
        

    @property
    def dial_position(self):
        attr = 'Setpoint_target'
        return self.proxy.read_attribute(attr).value / self.scaling_factor

    @dial_position.setter
    def dial_position(self, pos):
        attr = 'Setpoint_target'
        self.proxy.write_attribute(attr, pos * self.scaling_factor)

    def busy(self):
        attr = 'State'
        return not (self.proxy.read_attribute(attr).value == tango.DevState.ON)
