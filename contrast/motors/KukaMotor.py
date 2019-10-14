"""
Provides a Motor interface to the NanoMAX Kuka robot's Tango device,
https://gitlab.maxiv.lu.se/nanomax/dev-maxiv-kuka_robot
"""

import PyTango
from . import Motor

class KukaManager(object):
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

    def motor2index(self, motor):
        return self.polar_motors.index(motor)

    def _safe_get_pos(self):
        try:
            return self.proxy.position
        except PyTango.DevFailed:
            raise Exception('The robot device position is not available. State: %s' % self.proxy.State())

    def move_me(self, motor, pos):
        #### this is where movements need to be synchronized, i e
        #### take requests and don't start something new until the
        #### last request was done.
        target = self._safe_get_pos().copy()
        target[self.motor2index(motor)] = pos
        self.proxy.position = target

    def where_am_i(self, motor):
        current = self._safe_get_pos()
        return current[self.motor2index(motor)]

class KukaMotor(Motor):
    """
    Single motor as exposed by the KukaManager class above.
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
        state = self.manager.proxy.State()
        return not (state == PyTango.DevState.ON)

    def stop(self):
        self.manager.proxy.Stop()

