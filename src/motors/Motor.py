import time
import numpy as np
from collections import OrderedDict

from ..Gadget import Gadget
from ..environment import macro
from .. import utils

print(__name__)

class Motor(Gadget):
    """
    Should also handle limits and maybe user/dial units.
    """

    def move(self, pos):
        if self.busy():
            raise Exception('Motor is busy')
        # check limits here as well

    def position(self):
        raise NotImplementedError

    def busy(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

class DummyMotor(Motor):
    def __init__(self, *args, **kwargs):
        super(DummyMotor, self).__init__(*args, **kwargs)
        self._aim = 0.0
        self._oldpos = 0.0
        self._started = 0.0
        self.velocity = 1.0
    def move(self, pos):
        super(DummyMotor, self).move(pos)
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
    def __init__(self, *args):
        self.motors = args[::2]
        self.targets = np.array(args[1::2])
    
    def run(self):
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
    def __init__(self, *args):
        self.motors = args[::2]
        displacements = np.array(args[1::2])
        current = np.array([m.position() for m in self.motors])
        self.targets = current + displacements

@macro
class Wm(object):
    def __init__(self, *args):
        self.motors = args
    def run(self, *args):
        positions = tuple([m.position() for m in self.motors])
        dct = OrderedDict()
        for m, p in zip(self.motors, positions):
            print(m.name, p)

@macro
class Wa(Wm):
    def __init__(self):
        self.motors = [m for m in Motor.getinstances()]

@macro
class LsM(object):
    def run(self):
        dct = {m.name: m.__class__ for m in Motor.getinstances()}
        print(utils.dict_to_table(dct, titles=('name', 'class')))
