"""
Provides a ``Motor`` subclass for PiezoLEGS positioners controlled by a
Pmd401 controller via a MAX IV Tango device.
"""

import PyTango
import time
import math
from . import Motor
from . import PseudoMotor


class Pmd401Motor(Motor):
    """
    Single Pmd401 PiezoLEGS motor axis.
    """

    def __init__(self, device, axis, velocity=100, **kwargs):
        """
        :param device: Path to the Pmd401 Tango device
        :type device: str
        :param axis: Axis number on the controller
        :type axis: int
        :param ``**kwargs``: Passed on to the ``Motor`` base class
        """
        super(Pmd401Motor, self).__init__(**kwargs)
        self.proxy = PyTango.DeviceProxy(device)
        self.proxy.set_source(PyTango.DevSource.DEV)
        self._axis = int(axis)

    @property
    def dial_position(self):
        attr = 'channel%02d_encoder' % self._axis
        return self.proxy.read_attribute(attr).value

    @dial_position.setter
    def dial_position(self, pos):
        self.unpark()
        attr = 'channel%02d_position' % self._axis
        self.proxy.write_attribute(attr, pos)

    def busy(self):
        attr = 'channel%02d_state' % self._axis
        return (self.proxy.read_attribute(attr).value == 'running')

    def stop(self):
        self.proxy.StopAll()  # safety first

    def park(self):
        command = 'X%dM6' % self._axis
        reply = self.proxy.arbitrarySend(command)

    def unpark(self):
        command = 'X%dM2' % self._axis
        reply = self.proxy.arbitrarySend(command)


class BaseYMotor(PseudoMotor):
    """
    Pseudo motor which implements the y motion, combined by the
    longitudinal and wedge motion motors at the imaging.
    """
    z_part = math.cos(15/180*math.pi)
    y_part = -math.sin(15/180*math.pi)

    def calc_pseudo(self, physicals):
        pseudo = self.y_part * physicals[1]
        return pseudo

    def calc_physicals(self, pseudo):
        current_physicals = self.physicals()
        current_z = self.z_part * current_physicals[1] + current_physicals[0]
        physicals = [current_z - self.z_part * pseudo/self.y_part,
                     pseudo/self.y_part]
        return physicals


class BaseZMotor(PseudoMotor):
    """
    Pseudo motor which implements the z motion, combined by the
    longitudinal and wedge motion motors at the imaging.
    """
    z_part = math.cos(15/180*math.pi)
    y_part = -math.sin(15/180*math.pi)

    def calc_pseudo(self, physicals):
        pseudo = self.z_part * physicals[1] + physicals[0]
        return pseudo

    def calc_physicals(self, pseudo):
        current_physicals = self.physicals()
        physicals = [pseudo - self.z_part * current_physicals[1],
                     current_physicals[1]]
        return physicals
