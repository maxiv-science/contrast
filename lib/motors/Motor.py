import time
import numpy as np
from collections import OrderedDict

from ..Gadget import Gadget
from ..environment import macro, env
from .. import utils

class MotorLimitException(Exception):
    pass

class Motor(Gadget):
    """
    General base class for motors.

    Don't forget to call and check the return value of super().move in
    subclasses, as this checks motor limits!
    """

    def __init__(self, *args, **kwargs):
        super(Motor, self).__init__(*args, **kwargs)
        self._uplim = None
        self._lowlim = None
        self._format = '%.2f'

    def move(self, pos):
        if self.busy():
            raise Exception('Motor is busy')
        try:
            assert pos <= self._uplim
            assert pos >= self._lowlim
        except AssertionError:
            print('Trying to move %s outside its limits!' % self.name)
            return -1
        except TypeError:
            pass
        return 0

    def position(self):
        raise NotImplementedError

    def busy(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    @property
    def limits(self):
        return (self._lowlim, self._uplim)

    @limits.setter
    def limits(self, lims):
        lowlim, uplim = lims
        assert uplim > lowlim
        self._lowlim = lowlim
        self._uplim = uplim

class DummyMotor(Motor):
    def __init__(self, *args, **kwargs):
        super(DummyMotor, self).__init__(*args, **kwargs)
        self._aim = 0.0
        self._oldpos = 0.0
        self._started = 0.0
        self.velocity = 1.0
    def move(self, pos):
        if super(DummyMotor, self).move(pos) == 0:
            self._oldpos = self.position()
            self._started = time.time()
            self._aim = pos
    def position(self):
        dpos = self._aim - self._oldpos
        dt = time.time() - self._started
        T = abs(dpos / self.velocity)
        if dt < T:
            return self._oldpos + dpos * self.velocity * dt / T
        else:
            return self._aim
    def busy(self):
        return not np.isclose(self._aim, self.position())
    def stop(self):
        self._aim = self.position()

@macro
class Mv(object):
    """
    Move one or more motors.

    mvr <motor1> <position1> <motor2> <position2> ...

    """
    def __init__(self, *args):
        self.motors = args[::2]
        self.targets = np.array(args[1::2])
    
    def run(self):
        if max(m.userlevel for m in self.motors) > env.userLevel:
            print('You are trying to move motors above your user level!')
            return
        for m, pos in zip(self.motors, self.targets):
            m.move(pos)
        try:
            while True in [m.busy() for m in self.motors]:
                time.sleep(.01)
        except KeyboardInterrupt:
            for m in self.motors:
                m.stop()

@macro
class Mvr(Mv):
    """
    Move one or more motors relative to their current positions.

    mvr <motor1> <position1> <motor2> <position2> ...

    """
    def __init__(self, *args):
        self.motors = args[::2]
        displacements = np.array(args[1::2])
        current = np.array([m.position() for m in self.motors])
        self.targets = current + displacements

@macro
class Wm(object):
    """
    Print the positions of one or more motors.

    wm <motor1> <motor2> ...
    """
    def __init__(self, *args):
        self.motors = args
    def run(self, *args):
        names = [m.name for m in self.motors]
        vals = [m._format % m.position() for m in self.motors]
        lims = [str(m.limits) for m in self.motors]
        col1 = max([8,] + [len(s) + 2 for s in names])
        col2 = max([10,] + [len(s) + 2 for s in vals])
        col3 = max([8,] + [len(s) + 2 for s in lims])
        header = ('%%-%ss'%col1) % 'motor' \
                 + ('%%-%ss'%col2) % 'position' \
                 + ('%%-%ss'%col3) % 'limits'
        print('\n' + header)
        print('-' * len(header))
        for m, p, l in zip(names, vals, lims):
            line = ('%%-%ss'%col1) % m \
                   + ('%%-%ss'%col2) % p \
                   + ('%%-%ss'%col3) % l
            print(line)

@macro
class Wa(Wm):
    """
    Print the positions of all motors available at the current user level.
    """
    def __init__(self):
        self.motors = [m for m in Motor.getinstances()
                       if m.userlevel <= env.userLevel]

@macro
class LsM(object):
    """
    List available motors.
    """
    def run(self):
        dct = {m.name: m.__class__ for m in Motor.getinstances()
               if m.userlevel <= env.userLevel}
        print(utils.dict_to_table(dct, titles=('name', 'class')))

@macro
class SetLim(object):
    """
    Set limits on motors.

    setlim <motor1> <lower 1> <upper 1> ...
    """
    def __init__(self, *args):
        self.motors = args[::3]
        self.lowers = args[1::3]
        self.uppers = args[2::3]

    def run(self):
        for m, l, u in zip(self.motors, self.lowers, self.uppers):
            m.limits = (l, u)
