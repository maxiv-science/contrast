from .Scan import SoftwareScan
from .AScan import DScan
from ..environment import macro, MacroSyntaxError
from ..motors import all_are_motors
import numpy as np
import time

@macro
class SpiralScan(DScan):
    """
    Software scan across a 2D Archimedes spiral centered on the 
    current position. ::
        
        spiralscan <motor1> <motor2> <stepsize> <positions> <exp_time>
    """

    def __init__(self, m1, m2, stepsize, npos, exptime):
        # Parse arguments. We're inheriting DScan to get its nice run()
        # method, but we'll call the SoftwareScan constructor anyway bacause
        # we're not interested in DScan's way of parsing arguments.
        try:
            SoftwareScan.__init__(self, float(exptime))
            self.motors = [m1, m2]
            self.stepsize = float(stepsize)
            self.n_positions = int(npos)
            assert all_are_motors(self.motors)
        except:
            raise MacroSyntaxError

    def _generate_positions(self):
        starting = [m.position() for m in self.motors]
        for t in range(self.n_positions):
            A = self.stepsize * np.sqrt(t/np.pi)
            B = np.sqrt(4*np.pi*t)
            yield {self.motors[0].name: starting[0] + A * np.cos(B),
                   self.motors[1].name: starting[1] + A * np.sin(B)}
