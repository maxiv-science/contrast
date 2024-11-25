"""
Provides a ``Motor`` subclass for Smaract positioners. All numbers in
micrometers.

Controls these via a MAX IV Tango device,
https://gitlab.maxiv.lu.se/kits-maxiv/dev-maxiv-mcs
"""

try:
    import tango
except ImportError:
    pass
from . import Motor
import time


class SmaractLinearMotor(Motor):
    """
    Single Smaract motor axis.
    """
    def __init__(self, device, axis, velocity=None, frequency=None, **kwargs):
        """
        :param device: Path to the MCS Tango device
        :type device: str
        :param axis: Axis number on the controller
        :type axis: int
        :param velocity: Initialize velocity, defaults to None
        :type velocity: float
        :param ``**kwargs``: Passed on to the ``Motor`` base class
        """
        super().__init__(**kwargs)
        self.proxy = tango.DeviceProxy(device)
        self.proxy.set_source(tango.DevSource.DEV)
        self.axis = int(axis)
        if velocity is not None:
            attr = 'velocity_%d' % self.axis
            self.proxy.write_attribute(attr, velocity * 1e3)
        if frequency is not None:
            self.proxy.arbitraryCommand("SCLF%u,%u" % (self.axis, frequency))

    @property
    def dial_position(self):
        attr = 'position_%d' % self.axis
        return self.proxy.read_attribute(attr).value * 1e-3

    @dial_position.setter
    def dial_position(self, pos):
        attr = 'position_%d' % self.axis
        self.proxy.write_attribute(attr, pos * 1e3)

    def busy(self):
        attr = 'state_%d' % self.axis
        return not (self.proxy.read_attribute(attr).value == tango.DevState.ON)

    def home(self):
        print('\nhoming %s...' % self.name)
        self.proxy.arbitraryCommand("FRM%u,2,60000,1" % self.axis)
        while self.busy():
            time.sleep(.1)
        print('homing done')
    
    def frequency(self, freq):
        # set the maximum closed loop frequency of the positioner
        self.proxy.arbitraryCommand(f"SCLF{self.axis:d},{int(freq):d}")        

    def stop(self):
        self.proxy.stopOne(self.axis)  # safety first

    def health_check(self):
        # check if the encoder is in energy saving mode (not prefered) or always on (prefered)
        state_power_mode = self.proxy.read_attribute('power_mode').value
        if state_power_mode != 'enabled':
            print(f'\033[91m[!]\033[0m {self.name}: The motor is not in always on mode. Power Saving mode can result in lost positions.')
        # check if the stage is homed
        reference_position_known = self.proxy.read_attribute(f'physical_position_known_{self.axis}').value
        if reference_position_known != True:
            print(f'\033[91m[!]\033[0m {self.name}: The motor is not homed. SmarAct stages do not have absolute encoders.')

class SmaractRotationMotor(SmaractLinearMotor):
    @property
    def dial_position(self):
        attr = 'angle_%d' % self.axis
        result = self.proxy.read_attribute(attr).value
        result = result.split(',')
        pos = int(result[0])
        rev = int(result[1])
        pos = pos * 1e-6 + rev * 360
        return pos

    @dial_position.setter
    def dial_position(self, pos):
        angle = int(1e6 * (pos % 360))
        rev = int(pos // 360)
        attr = 'angle_%d' % self.axis
        val = '%d,%d' % (angle, rev)
        self.proxy.write_attribute(attr, val)

class SmaractLinearMotor_MCS2(SmaractLinearMotor):

    def stop(self):
        self.proxy.stop(self.axis)  # no stopone for MCS2... yet

class SmaractRotationMotor_MCS2(SmaractLinearMotor):

    @property
    def dial_position(self):
        attr = 'position_%d' % self.axis
        val = self.proxy.read_attribute(attr).value
        pos = val * 3.1415 * 2.50
        return pos

    @dial_position.setter
    def dial_position(self, pos):
        attr = 'position_%d' % self.axis
        val = pos / 3.1415 / 2.50
        self.proxy.write_attribute(attr, val)
