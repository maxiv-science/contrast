from .Scan import SoftwareScan
from ..environment import macro, MacroSyntaxError
from ..motors import all_are_motors
import numpy as np
import time

@macro
class Mesh(SoftwareScan):
    """
    Software scan on a regular grid of N motors.
        
    mesh <motor1> <start> <stop> <intervals> ... <exp_time>
    """

    def __init__(self, *args):
        """
        Parse arguments.
        """
        self.motors = []
        self.limits = []
        self.intervals = []
        try:
            exposuretime = float(args[-1])
            super(Mesh, self).__init__(exposuretime)
            for i in range(int((len(args) - 1) / 4)):
                self.motors.append(args[4*i])
                self.limits.append([float(m) for m in args[4*i+1:4*i+3]])
                self.intervals.append(int(args[4*i+3]))
            assert all_are_motors(self.motors)
            assert (len(args) - 1) % 4 == 0
        except:
            raise MacroSyntaxError

    def _generate_positions(self):
        positions = []
        for i in range(len(self.motors)):
            positions.append(np.linspace(self.limits[i][0],
                                         self.limits[i][1],
                                         self.intervals[i]+1))
        grids = np.meshgrid(*reversed(positions))
        grids = [l for l in reversed(grids)] # fastest last
        for i in range(len(grids[0].flat)):
            yield {m.name: pos.flat[i] for (m, pos) in zip(self.motors, grids)}

@macro
class DMesh(Mesh):
    """
    Software scan on a regular grid of N motors, with positions relative
    to each motor's current one. Moves motors back at the end.

    dmesh <motor1> <start> <stop> <intervals> ... <exp_time>
    """
    def _generate_positions(self):
        current = {m.name:m.position() for m in self.motors}
        for pos in super(DMesh, self)._generate_positions():
            for i, m in enumerate(self.motors):
                pos[m.name] += current[m.name]
            yield pos

    def run(self):
        old_pos = [m.position() for m in self.motors]
        super(DMesh, self).run()
        # wait for motors then move them back
        while True in [m.busy() for m in self.motors]:
            time.sleep(.01)
        print('Returning motors to their starting positions...')
        for m, pos in zip(self.motors, old_pos):
            m.move(pos)
        while True in [m.busy() for m in self.motors]:
            time.sleep(.01)
        print('...done')
