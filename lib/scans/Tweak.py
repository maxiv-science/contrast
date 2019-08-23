from ..environment import macro, MacroSyntaxError
from .Mesh import Mesh
import tty, sys, termios
from ..motors import all_are_motors

# constants to keep track of key buttons
KEY_UP = '\x1b[A'
KEY_DOWN = '\x1b[B'
KEY_RIGHT = '\x1b[C'
KEY_LEFT = '\x1b[D'

def getarrowkey():
    """
    A function which waits for a keypress and returns one of the above constants.
    """
    ch = None
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(sys.stdin.fileno())
        ch = sys.stdin.read(3)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    if ch in (KEY_UP, KEY_DOWN, KEY_RIGHT, KEY_LEFT):
        return ch
    else:
        return None

@macro
class Tweak(Mesh):
    """
    An interactive scan where motor positions are chosen manually for
    each point. Useful for tweaking motors and reading the currently
    active detectors after each step.

    tweak <motor1> <stepsize1> [<motor2> <stepsize2>] <exp_time>
    """

    def __init__(self, *args):
        """
        Parse arguments.
        """
        try:
            exposuretime = float(args[-1])
            super(Mesh, self).__init__(exposuretime)
            self.motors = args[:-1:2]
            self.steps = args[1::2]
            assert len(args) in (3, 5)
            assert all_are_motors(self.motors)
        except:
            raise
            raise MacroSyntaxError
        print('\nUse the arrow keys to tweak motors and ctrl-C to stop.')

    def _generate_positions(self):
        positions = {m.name:m.position() for m in self.motors}
        yield positions
        while True:
            key = getarrowkey()
            imotor = 0 if key in (KEY_LEFT, KEY_RIGHT) else -1
            direction = -1 if key in (KEY_DOWN, KEY_LEFT) else 1
            positions[self.motors[imotor].name] += direction * self.steps[imotor]
            yield positions

    def _before_move(self):
        # Override so as not to respect the scheduler.
        pass
