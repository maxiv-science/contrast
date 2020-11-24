"""
Provides a Motor interface to the `MAX IV Kuka robot Tango device`_.

.. _MAX IV Kuka robot Tango device: https://gitlab.maxiv.lu.se/nanomax/dev-maxiv-kuka_robot
"""

import PyTango
import time
from . import Motor

class KukaRobot(object):
    """
    Managing class which coordinates movements of the robot in polar
    coordinates. The manager's role is to avoid trying to move more than one
    robot motor at a time, which would not be compatible with the controller.

    This class owns three ``KukaMotor`` instances, which are returned on
    iteration::

        gamma, delta, radius = KukaRobot('path/to/device', names=['gamma, 'delta', 'radius'])
    """
    def __init__(self, tango_path, names=['gamma', 'delta', 'radius']):
        """
        :param tango_path: Path to the underlying Tango device
        :type tango_path: str
        :param names: Names to assign to the three polar motors
        :type names: list, tuple
        """
        self.proxy = PyTango.DeviceProxy(tango_path)
        self.proxy.set_source(PyTango.DevSource.DEV)
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
        Method which makes sure that only one polar axis is moved at a time.
        For now, this is done by blocking until the device is standing still.
        Should perhaps be threaded or so, but works like this for scanning for
        example the two polar angles in a mesh.

        :param motor: Motor instance to move, typically ``self`` for the calling ``KukaMotor``.
        :param pos: Target position
        :type pos: float
        """
        while self.busy():
            time.sleep(.5)
        target = self._safe_get_pos().copy()
        target[self.motor2index(motor)] = pos
        ok = False
        while not ok:
            try:
                self.proxy.position = target
                ok = True
            except PyTango.DevFailed:
                print('robot movement failed. reinizializing etc...')
                self.proxy.Init()
                time.sleep(1)
                self.proxy.Connect()
                time.sleep(1)

    def where_am_i(self, motor):
        current = self._safe_get_pos()
        return current[self.motor2index(motor)]

    def busy(self):
        return not (self.proxy.State() == PyTango.DevState.ON)

class KukaMotor(Motor):
    """
    Single motor as exposed by the ``KukaRobot`` class.
    """

    def __init__(self, manager, **kwargs):
        """
        :param manager: Managing ``KukaRobot`` instance
        :param ``**kwargs``: Passed on to the base class constructor
        """
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
        This motor needs to override the base class move, because move
        commands must be accepted even if the motor is busy.

        :param pos: Target position
        :type pos: float
        """
        dial = (pos - self._offset) / self._scaling
        _lowlim, _uplim = self.dial_limits
        try:
            assert dial <= _uplim
            assert dial >= _lowlim
        except AssertionError:
            print('Trying to move %s outside its limits!' % self.name)
            return -1
        except TypeError:
            pass
        self.dial_position = dial

