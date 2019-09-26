import time
import numpy as np
from ..environment import macro, env
from ..recorders import active_recorders, RecorderHeader, RecorderFooter
from ..detectors import Detector

class SoftwareScan(object):
    """
    Base class for the normal sardana-style software-controlled scan. Respects
    the availability and deadlines managed by env.scheduler.

    Overwrite these methods:
        __init__ (which reads in the scan parameters) and
        _generate_positions (which generates the line scan, mesh, spiral, or what ever you like)
    """

    def __init__(self, exposuretime):
        """
        The constructor should parse parameters.
        """
        self.motors = []   # list of motors, to be filled by subclass
        self.exposuretime = exposuretime
        self.scannr = env.nextScanID
        env.nextScanID += 1

    def header_line(self):
        motor_names = [m.name for m in self.motors]
        group = Detector.get_active_detectors()
        det_names = [d.name for d in group]
        header = '#       ' + len(motor_names) * '%-8s' + len(group) * '%-14s' + 'dt'
        line = '-' * (8 + len(motor_names) * 8 + len(group) * 16 + 8)
        return ('\n' + header + '\n' + line) % tuple(motor_names + det_names)

    def table_line(self):
        group = Detector.get_active_detectors()
        return '%-8d' + len(self.motors) * '%-8.2f' + len(group) * '%-12s  ' + '%-8.2f'

    def format_number(self, nr):
        if isinstance(nr, dict):
            return '<%d-dict>' % len(nr)
        try:
            return '%8s' % (nr.shape,)
        except:
            pass
        try:
            return '%8e' % nr
        except TypeError:
            return str(nr)[-8:]

    def _calc_time_needed(self):
        """
        Suggestion for how to organize topup avoidance. You could 
        also look at how long acquisitions have tended to take. Or
        you could try to estimate the time needed based on the
        input parameters.
        """
        return self.exposuretime * 5 + 5

    def _before_move(self):
        """
        Gets called for each step.
        """

        # Example implementation of topup avoidance
        time_needed = self._calc_time_needed()
        enough_time = time_needed < env.scheduler.limit if env.scheduler.limit else True
        ready = env.scheduler.ready
        while not ready or not enough_time:
            if not enough_time:
                print('not enough time to complete this measurement, so waiting...')
            else:
                print('Waiting for beamline to become available...')
            time.sleep(1.)
            enough_time = time_needed < env.scheduler.limit
            ready = env.scheduler.ready

    def _before_arm(self):
        """
        Gets called for each step.
        """
        pass

    def _while_acquiring(self):
        """
        Gets called repeatedly while the detectors detect.
        """
        pass

    def _before_start(self):
        """
        Gets called for each step.
        """
        pass

    def run(self):
        """
        This method does all the serious interaction with motors,
        detectors, and data recorders.
        """
        print('\nScan #%d starting at %s' % (self.scannr, time.asctime()))
        print(self.header_line())
        positions = self._generate_positions()
        table_line = self.table_line()
        # find and prepare the detectors
        group = Detector.get_active_detectors()
        if group.busy():
            print('Detectors are busy: %s' % (', '.join([d.name for d in group if d.busy()])))
            return
        group.prepare(self.exposuretime, self.scannr)
        t0 = time.time()
        # send a header to the recorders
        snap = env.snapshot.capture()
        for r in active_recorders():
            r.queue.put(RecorderHeader(scannr=self.scannr, path=env.paths.directory, snapshot=snap))
        try:
            for i, pos in enumerate(positions):
                # move motors
                self._before_move()
                for m in self.motors:
                    m.move(pos[m.name])
                while True in [m.busy() for m in self.motors]:
                    time.sleep(.01)
                # arm detectors
                self._before_arm()
                group.arm()
                # start detectors
                self._before_start()
                group.start()
                while group.busy():
                    self._while_acquiring()
                    time.sleep(.01)
                # read detectors and motors
                dt = time.time() - t0
                dct = {'dt': dt}
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
            print('\nScan #%d ending at %s' % (self.scannr, time.asctime()))
        except KeyboardInterrupt:
            group.stop()
            print('\nScan #%d cancelled at %s' % (self.scannr, time.asctime()))

        # tell the recorders that the scan is over
        for r in active_recorders():
            r.queue.put(RecorderFooter())
        
    def _generate_positions(self):
        """
        Function or generator which returns or yields an iterable of
        dicts {motorA.name: posA, motorB.name: posB, ...}
        """
        raise NotImplementedError

@macro
class LoopScan(SoftwareScan):
    """
    A software scan with no motor movements. Number of exposures is
    <intervals> + 1, for consistency with ascan, dscan etc.

    loopscan <intervals> <exp_time>
    """
    def __init__(self, intervals, exposuretime=1.0):
        """
        Parse arguments.
        """
        super(LoopScan, self).__init__(float(exposuretime))
        self.intervals = intervals
        self.motors = []

    def _generate_positions(self):
        # dummy positions with a non existent motor
        for i in range(self.intervals + 1):
            yield {'fake':i}

@macro
class Ct(object):
    """
    Make a single acquisition on the active detectors without recording
    data. Optional argument <exp_time> specifies exposure time, the default
    is 1.0.

    ct [<exp_time>]
    """
    def __init__(self, exp_time=1, print_nd=True):
        """
        Parse arguments.
        """
        self.exposuretime = float(exp_time)

    def run(self):
        # find and prepare the detectors
        group = Detector.get_active_detectors()
        group.prepare(self.exposuretime, dataid=None)
        # arm and start detectors
        group.arm()
        while group.busy():
            time.sleep(.01)
        group.start()
        while group.busy():
            time.sleep(.01)
        # read detectors and motors
        dct = {}
        for d in group:
            dct[d.name] = d.read()
        # print results
        for key, val in dct.items():
            try:
                val_ = val.shape
            except AttributeError:
                val_ = val
            print(key, ':', val_)
