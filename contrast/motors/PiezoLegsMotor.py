"""
Provides a ``Motor`` subclass for PiezoLEGS positioners controlled by a
Pmd401 controller via a MAX IV Tango device: https://gitlab.maxiv.lu.se/kits-maxiv/dev-maxiv-pmd401.
"""

import PyTango
import time
import math
from . import Motor
from . import PseudoMotor


class ImgSampleStage(object):
    """
    Managing class which coordinates movements of the imaging station sample base stage to 
    achive the Y and Z motions through combination of the horizontal Z motor and the wedge Y motor. 
    The manager's role is to always move the motors away from the sample and then approach 
    to the final position, to avoid collitions with the OSA. It also Y or Z motions one at a time. 

    This class owns three ``PiezoLegsMotor`` instances, which are returned on
    iteration::

        bx, by, bz = ImgSampleStage('path/to/device',
                                         names=['bx', 'by', 'bz'])
    """

    def __init__(self, device, velocity=100, names=['bx', 'by', 'bz'], **kwargs):
        """
        :param device: Path to the underlying Tango device
        :type device: str
        :param velocity: Motion velocity in full step units/sec
        :type device: int
        :param names: Names to assign to the three virtual motors x, y, z
        :type names: list, tuple
        """
        self.proxy = PyTango.DeviceProxy(device)
        self.proxy.set_source(PyTango.DevSource.DEV)
        self.axis_motors = [
            AxisMotor(manager=self, name=names[0], **kwargs),
            AxisMotor(manager=self, name=names[1], **kwargs),
            AxisMotor(manager=self, name=names[2], **kwargs)
        ]
        self.y_part = math.sin(-15/180 * math.pi)
        self.z_part = math.cos(-15/180 * math.pi)

    def __iter__(self):
        return self.axis_motors.__iter__()

    def motor2index(self, motor):
        return self.axis_motors.index(motor)

    def move_me(self, motor, pos):
        """
        Method which makes sure that only one of the vertical (Y) or longitudinal (Z) axis are 
        moved at a time. This is required because both these axis are realized by a combination 
        of the longitudinal motor (motor 1) and the wedge motor (number 2). 
        Motor 0 is equal to the X-axis. Since the X-motion is independet of all other motors,
        this can be operated independent.  

        :param motor: Motor instance to move, typically ``self`` for the calling ``AxisMotor``.
        :param pos: Target position
        :type pos: float
        """
        while self.busy(motor):
            time.sleep(.5)

        if self.motor2index(motor) == 0:
            # Sets the x-position. Moves the horizontal x-direction motor. Simple, this is only one physical motor
            self.unpark()
            self.proxy.write_attribute('channel00_position', pos)
        elif self.motor2index(motor) == 1:
            # Sets the y-position. This is achieved by a combination of the height wedge motor and the z-motor.
            # When the height is changed, the wedge AND the z-direction motor needs to be moved to result in
            # new height and maintained z-position.
            current_wedge = self.proxy.read_attribute('channel02_encoder').value
            current_long = self.proxy.read_attribute('channel01_encoder').value
            new_wedge = pos / self.y_part
            new_long = current_long - self.z_part * (new_wedge - current_wedge)
            # Ensures that the sample is moving away from the OSA and then approached with the other motor
            if new_long > current_long:
                self.proxy.write_attribute('channel01_position', new_long)
                while self.busy(motor):
                    time.sleep(.1)
                self.proxy.write_attribute('channel01_position', new_wedge)
                while self.busy(motor):
                    time.sleep(.1)
            else:
                self.proxy.write_attribute('channel01_position', new_wedge)
                while self.busy(motor):
                    time.sleep(.1)
                self.proxy.write_attribute('channel01_position', new_long)
                while self.busy(motor):
                    time.sleep(.1)
        elif self.motor2index(motor) == 2:
            # Sets the z-position. THis is achieved by the combined motion of the longitudinal motor
            # and the horizontal part of th wedge motor.
            new_long = pos - self.z_part * self.proxy.read_attribute('channel02_encoder').value
            self.proxy.write_attribute('channel01_position', new_long)
            while self.busy(motor):
                time.sleep(.1)

    def where_am_i(self, motor):
        """
        Returns the horizontal, vertical or longitudinal position. The vertical position is calculated 
        from the wedge angle (15 degrees) of the stage. The longitudinal position results from both the 
        wedge position and the z-direction position. The horizontal axis is in fact the physical motor
        position

        :param motor: Motor instance to move, typically ``self`` for the calling ``AxisMotor``.
        """
        if self.motor2index(motor) == 0:
            position = self.proxy.read_attribute('channel00_encoder').value
        elif self.motor2index(motor) == 1:
            position = self.y_part * self.proxy.read_attribute('channel02_encoder').value
        elif self.motor2index(motor) == 2:
            position = self.z_part * \
                self.proxy.read_attribute('channel02_encoder').value + self.proxy.read_attribute('channel01_encoder').value
        return position

    def busy(self, motor):
        if self.motor2index(motor) == 0:
            busy = self.proxy.read_attribute('channel00_state').value == 'running'
        elif self.motor2index(motor) > 0:
            busy = self.proxy.read_attribute('channel01_state').value == 'running' or self.proxy.read_attribute('channel02_state').value == 'running'
        return busy

    def stop(self, motor):
        self.proxy.StopAll()


class AxisMotor(Motor):
    """
    Single motor as exposed by the ``ImgSampleStage`` class. For the X-axis, it is directly operating the 
    physical motor. For the Y- and Z-axis the respective positions are achieved by combination position
    for the longitudinal motor and the wedge motor. 
    """

    def __init__(self, manager, **kwargs):
        """
        :param manager: Managing ``ImgSampleStage`` instance
        :param ``**kwargs``: Passed on to the base class constructor
        """
        super(AxisMotor, self).__init__(**kwargs)
        self.manager = manager

    @property
    def dial_position(self):
        return self.manager.where_am_i(motor=self)

    @dial_position.setter
    def dial_position(self, pos):
        self.manager.move_me(motor=self, pos=pos)

    def busy(self):
        return self.manager.busy(motor=self)

    def stop(self):
        self.manager.Stop(motor=self)

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


class PiezoLegsMotor(Motor):
    """
    Single Pmd401 PiezoLEGS motor axis.
    """

    def __init__(self, device, axis, velocity=100, **kwargs):
        """
        :param device: Path to the Pmd401 Tango device
        :type device: str
        :param axis: Axis number on the controller
        :type axis: int
        :param velocity: Velocity for the motor. Arbitrary value
        :type velocity: int
        :param ``**kwargs``: Passed on to the ``Motor`` base class
        """
        super(PiezoLegsMotor, self).__init__(**kwargs)
        self.proxy = PyTango.DeviceProxy(device)
        self.proxy.set_source(PyTango.DevSource.DEV)
        self._axis = int(axis)
        self._velocity = velocity

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


class BaseYMotor(Motor):
    """
    Pseudo motor which implements the y motion, combined by the
    longitudinal and wedge motion motors at the imaging.
    """
    z_part = math.cos(15 / 180 * math.pi)
    y_part = -math.sin(15 / 180 * math.pi)

    def calc_pseudo(self, physicals):
        pseudo = self.y_part * physicals[1]
        return pseudo

    def calc_physicals(self, pseudo):
        current_physicals = self.physicals()
        current_z = self.z_part * current_physicals[1] + current_physicals[0]
        physicals = [current_z - self.z_part * pseudo / self.y_part,
                     pseudo / self.y_part]
        return physicals


class BaseZMotor(Motor):
    """
    Pseudo motor which implements the z motion, combined by the
    longitudinal and wedge motion motors at the imaging.
    """
    z_part = math.cos(15 / 180 * math.pi)
    y_part = -math.sin(15 / 180 * math.pi)

    def calc_pseudo(self, physicals):
        pseudo = self.z_part * physicals[1] + physicals[0]
        return pseudo

    def calc_physicals(self, pseudo):
        current_physicals = self.physicals()
        physicals = [pseudo - self.z_part * current_physicals[1],
                     current_physicals[1]]
        return physicals
