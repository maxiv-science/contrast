from .Scan import SoftwareScan
from ..environment import macro, MacroSyntaxError
from ..motors import all_are_motors
import numpy as np
import time

@macro
class AScan(SoftwareScan):
    """
    Software scan one or more motors in parallel. ::
        
        ascan <motor1> <start> <stop> ... <intervals> <exp_time>
    """

    def __init__(self, *args):
        self.motors = []
        self.limits = []
        try:
            exposuretime = float(args[-1])
            self.intervals = int(args[-2])
            super(AScan, self).__init__(exposuretime)
            for i in range(int((len(args) - 2) / 3)):
                self.motors.append(args[3*i])
                self.limits.append([float(m) for m in args[3*i+1:3*i+3]])
            self.n_positions = self.intervals + 1
            assert all_are_motors(self.motors)
            assert (len(args) - 2) % 3 == 0
        except:
            raise MacroSyntaxError

    def _generate_positions(self):
        positions = []
        for i in range(len(self.motors)):
            positions.append(np.linspace(self.limits[i][0],
                                         self.limits[i][1],
                                         self.intervals+1))
        for i in range(len(positions[0])):
            yield {m.name: pos[i] for (m, pos) in zip(self.motors, positions)}

@macro
class DScan(AScan):
    """
    Software scan one or more motors in parallel, with positions
    relative to each motor's current one. Moves back afterwards. ::

        dscan <motor1> <start> <stop> <intervals> ... <exp_time>
    """
    def _generate_positions(self):
        current = {m.name:m.position() for m in self.motors}
        for pos in super(DScan, self)._generate_positions():
            for i, m in enumerate(self.motors):
                pos[m.name] += current[m.name]
            yield pos

    def run(self):
        old_pos = [m.position() for m in self.motors]
        super(DScan, self).run()
        # wait for motors then move them back
        while True in [m.busy() for m in self.motors]:
            time.sleep(.01)
        print('Returning motors to their starting positions...')
        for m, pos in zip(self.motors, old_pos):
            m.move(pos)
        while True in [m.busy() for m in self.motors]:
            time.sleep(.01)
        print('...done')
