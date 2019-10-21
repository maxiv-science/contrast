"""
Provides a Motor interface to the NanoMAX Kuka robot's Tango device,
https://gitlab.maxiv.lu.se/nanomax/dev-maxiv-kuka_robot
"""

import PyTango
import time
from . import Motor

class KukaRobot(object):
    """
    Managing class which coordinates movements of the robot
    in polar coordinates. The manager's role is to avoid
    trying to move more than one robot motor at a time, which
    would not be compatible with the controller.
    """
    def __init__(self, tango_path, names=['gamma', 'delta', 'radius']):
        self.proxy = PyTango.DeviceProxy(tango_path)
        self.polar_motors = [
            KukaMotor(manager=self, name=names[0]),
            KukaMotor(manager=self, name=names[1]),
            KukaMotor(manager=self, name=names[2]),]

    def __iter__(self):
        return self.polar_motors.__iter__()

    def motor2index(self, motor):
        return self.polar_motors.index(motor)

    def _safe_get_pos(self):
        try:
            return self.proxy.position
        except PyTango.DevFailed:
            raise Exception('The robot device position is not available. State: %s' % self.proxy.State())

    def move_me(self, motor, pos):
        """
        For now, this method just blocks until the device
        is standing still. Should perhaps be threaded or so,
        but works like this for scanning for example gamma
        and delta in a mesh.
        """
        while self.busy():
            time.sleep(.5)
        target = self._safe_get_pos().copy()
        target[self.motor2index(motor)] = pos
        self.proxy.position = target

    def where_am_i(self, motor):
        current = self._safe_get_pos()
        return current[self.motor2index(motor)]

    def busy(self):
        return not (self.proxy.State() == PyTango.DevState.ON)

class KukaMotor(Motor):
    """
    Single motor as exposed by the KukaRobot class above.
    """

    def __init__(self, manager, **kwargs):
        super(KukaMotor, self).__init__(**kwargs)
        self.manager = manager

    @property
    def dial_position(self):
        return self.manager.where_am_i(motor=self)

    @dial_position.setter
    def dial_position(self, pos):
        self.manager.move_me(motor=self, pos=pos)

    def busy(self):
        return self.manager.busy()

    def stop(self):
        self.manager.proxy.Stop()

    def move(self, pos):
        """
        This motor needs to override the base class move, because
        move commands must be accepted even if the motor is busy.
        """
        dial = (pos - self._offset) / self._scaling
        try:
            assert dial <= self._uplim
            assert dial >= self._lowlim
        except AssertionError:
            print('Trying to move %s outside its limits!' % self.name)
            return -1
        except TypeError:
            pass
        self.dial_position = dial

