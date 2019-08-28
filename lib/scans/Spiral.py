from .Scan import SoftwareScan
from ..environment import macro, MacroSyntaxError
from ..motors import all_are_motors
import numpy as np
import time

@macro
class SpiralScan(SoftwareScan):
    """
    Software scan across a 2D Archimedes spiral centered on the 
    current position.
        
    spiralscan <motor1> <motor2> <stepsize> <positions> <exp_time>
    """

    def __init__(self, *args):
        """
        Parse arguments.
        """
        try:
            assert len(args) == 5
            super(SpiralScan, self).__init__(float(args[4]))
            self.motors = args[:2]
            self.stepsize = float(args[2])
            self.npos = int(args[3])
            assert all_are_motors(self.motors)
        except:
            raise MacroSyntaxError

    def _generate_positions(self):
        for t in range(self.npos):
            A = self.stepsize * np.sqrt(t/np.pi)
            B = np.sqrt(4*np.pi*t)
            yield {self.motors[0].name: self.old_pos[0] + A * np.cos(B),
                   self.motors[1].name: self.old_pos[1] + A * np.sin(B)}

    def run(self):
        """
        Override this just to get back to the starting positions afterwards.
        """
        self.old_pos = [m.position() for m in self.motors]
        super(SpiralScan, self).run()
        # wait for motors then move them back
        while True in [m.busy() for m in self.motors]:
            time.sleep(.01)
        print('Returning motors to their starting positions...')
        for m, pos in zip(self.motors, self.old_pos):
            m.move(pos)
        while True in [m.busy() for m in self.motors]:
            time.sleep(.01)
        print('...done')
