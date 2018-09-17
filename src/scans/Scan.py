import time
import numpy as np
from ..environment import macro, env
from ..recorders import active_recorders

print(__name__)

class SoftwareScan(object):
    """
    Base class for the normal sardana-style software-controlled scan.
    Overwrite these methods:
        __init__ (which reads in the scan parameters) and
        _generate_positions (which generates the line scan, mesh, spiral, or what ever you like)
    """

    def __init__(self, *args):
        """
        The constructor should parse parameters.
        """
        self.motors = []         # list of motors, the order is preserved.
        self.exposuretime = None # needs to be initialized!
        self.scannr = env.nextScanID
        env.nextScanID += 1

    def header_line(self):
        motor_names = [m.name for m in self.motors]
        group = env.currentDetectorGroup
        det_names = [d.name for d in group]
        header = '#       ' + len(motor_names) * '%-8s' + len(group) * '%-14s' + 'dt'
        line = '-' * (8 + len(motor_names) * 8 + len(group) * 16 + 8)
        return ('\n' + header + '\n' + line) % tuple(motor_names + det_names)

    def table_line(self):
        group = env.currentDetectorGroup
        return '%-8d' + len(self.motors) * '%-8.2f' + len(group) * '%-12s  ' + '%-8.2f'

    def format_number(self, nr):
        try:
            return '%8e' % nr
        except TypeError:
            return str(nr)[-8:]

    def run(self):
        """
        This method does all the serious interaction with motors and
        Detectors.
        """
        positions = self._generate_positions()
        print(self.header_line())
        table_line = self.table_line()
        # find and prepare the detectors
        group = env.currentDetectorGroup
        group.prepare(self.exposuretime)
        t0 = time.time()
        for i in range(len(list(positions.values())[0])):
            # move motors
            for m in self.motors:
                m.move(positions[m.name][i])
            while True in [m.busy() for m in self.motors]:
                time.sleep(.01)
            # arm and start detectors
            group.arm()
            group.start()
            while group.busy():
                time.sleep(.01)
            # read detectors and motors
            dt = time.time() - t0
            dct = {'dt': dt, 'scannr': self.scannr}
            for d in group:
                dct[d.name] = d.read()
            for m in self.motors:
                dct[m.name] = m.position()
            # pass data to recorders
            for r in active_recorders():
                r.queue.put(dct)
            # print spec-style info
            print(table_line % tuple([i] + 
                  [m.position() for m in self.motors]
                  + [self.format_number(dct[d.name]) for d in group] 
                  + [dt]))
        
    def _generate_positions(self):
        """
        Function which returns ordered dict {motor.name: (pos0, pos1, pos2, ...)}.
        """
        raise NotImplementedError


@macro
class AScan(SoftwareScan):
    """
    Software scan on a regular grid of N motors.

    General syntax the same as spock ascan and mesh:
        
        scan_command motor1 start stop intervals ... exp_time
    """

    def __init__(self, *args):
        """
        Parse arguments.
        """
        super(AScan, self).__init__(*args)
        self.exposuretime = float(args[-1])
        self.motors = []
        self.limits = []
        self.intervals = []
        for i in range(int((len(args) - 1) / 4)):
            self.motors.append(args[4*i])
            self.limits.append([float(m) for m in args[4*i+1:4*i+3]])
            self.intervals.append(int(args[4*i+3]))

    def _generate_positions(self):
        positions = []
        size = 1
        for i in range(len(self.motors)):
            positions.append(np.linspace(self.limits[i][0],
                                         self.limits[i][1],
                                         self.intervals[i]+1))
        grids = np.meshgrid(*reversed(positions))
        grids = [l for l in reversed(grids)] # fastest last
        return {m.name: pos.flatten() for (m, pos) in zip(self.motors, grids)}


@macro
class DScan(AScan):
    def _generate_positions(self):
        positions = super(DScan, self)._generate_positions()
        for i, m in enumerate(self.motors):
            positions[m.name] += m.position()
        return positions
    def run(self):
        old_pos = [m.position() for m in self.motors]
        super(DScan, self).run()
        print('Returning motors to their starting positions...')
        for m, pos in zip(self.motors, old_pos):
            m.move(pos)
        while True in [m.busy() for m in self.motors]:
            time.sleep(.01)
        print('...done')
