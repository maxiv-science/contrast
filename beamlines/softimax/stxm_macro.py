from contrast.environment import env, macro, MacroSyntaxError
from contrast.scans import SoftwareScan
from contrast.detectors import Detector
from contrast.recorders import active_recorders
import numpy as np
import time


@macro
class Stxm(SoftwareScan):
    """
    Sample stxm for softimax.
        
    stxm <fast motor> <start> <stop> <intervals> <slow motor> <start> <stop> <intervals> <exp time> <latency>

    """

    SLEEP = .01
    FAST = 1000
    MARGIN = 1.
    PANDA = 'B318A-EA01/CTL/PandaPosTrig'

    def __init__(self, *args, **kwargs):
        """
        Parse and check arguments.
        """
        
        if len(args) < 10:
            raise ValueError('Not enough parameters. See "%stxm?" for usage.')

        (self.fast_motor, self.fast_begin, self.fast_end, self.fast_ints,
         self.slow_motor, self.slow_begin, self.slow_end, self.slow_ints,
         self.exptime, self.latency) = args

        # make sure the fast motor has a velocity or proxy.velocity attribute
        if hasattr(self.fast_motor, 'velocity'):
            ok = True
            self.proxy_attr = False
        elif hasattr(self.fast_motor, 'proxy'):
            if hasattr(self.fast_motor.proxy, 'Velocity'):
                ok = True
                self.proxy_attr = True
        if not ok:
            raise ValueError('Fast motor must have .velocity or .proxy.velocity attribute')

        super().__init__(self.exptime)

    def run(self):
        """
        Run the actual scan. These little hooks can be included for full
        compatibility with SoftwareScan (opening shutters, printing
        progress, etc):

            self._before_scan()
            self._before_move()
            self._before_arm()
            self._before_start()
            self._while_acquiring()
            self._after_scan()
        """

        # Pre-scan stuff (incl snapshots and detector preparation)
        self._before_scan()
        self._setup()
        print('\nScan #%d starting at %s' % (self.scannr, time.asctime()))
        
        # The panda is a special device here, not just a detector.
        if self.PANDA:
            # real pandabox
            panda = DeviceProxy(self.PANDA)
        else:
            # dummy panda object
            panda = DummyPanda()
        panda.DetPosCapt = True

        try:
            slow_positions = np.linspace(
                                 self.slow_begin, self.slow_end, self.slow_ints + 1
                             )
            for y_i, y_val in enumerate(slow_positions):
                # move to the next line
                self._before_move()
                self.slow_motor.move(y_val)
                while self.slow_motor.busy():
                    time.sleep(.01)

                # arm detectors (like triggered ones)
                self._before_arm()
                self.group.arm()

                # start detectors (like not triggered ones)
                self._before_start()
                self.group.start(trials=10)

                # run the stxm line
                ax = 'Y' if ('y' in self.fast_motor.name) else 'X'
                self._do_line(self.fast_motor, self.fast_begin, self.fast_end,
                              self.fast_ints, self.exptime, self.latency, panda, ax)

                while (panda.PointNOut is None
                       or (len(panda.PointNOut) < self.fast_ints)
                       or self.fast_motor.busy()
                       or self.group.busy()):
                    self._while_acquiring()
                    time.sleep(.01)

                # read detectors and panda
                dt = time.time() - self.t0
                dct = OrderedDict()
                for d in self.group:
                    dct[d.name] = d.read()
                dct['dt'] = dt

                # pass data to recorders
                for r in active_recorders():
                    r.queue.put(dct)

                # print spec-style info
                self.output(i, dct.copy())

            print('\nScan #%d ending at %s' % (self.scannr, time.asctime()))
                
        except KeyboardInterrupt:
            return

    def _setup(self):
        # find and prepare the detectors
        self.group = Detector.get_active()
        self.group.prepare(self.exposuretime, self.scannr, self.slow_ints + 1, trials=10)
        self.t0 = time.time()
        # send a header to the recorders
        snap = env.snapshot.capture()
        for r in active_recorders():
            r.queue.put(RecorderHeader(scannr=self.scannr, 
                                       status='started',
                                       path=env.paths.directory,
                                       snapshot=snap, 
                                       description=self._command))

    def _set_vel(self, vel):
        if self.proxy_attr:
            self.fast_motor.proxy.Velocity = vel
        else:
            self.fast_motor.velocity = vel

    def _do_line(self, motor, start, end, N, exptime, latency, panda, axis):
        panda.TrigAxis = axis # triger axis X or Y for horizontal and vertical respectively
        panda.TrigXPos = float(start) # position in microns
        panda.DetTimePulseStep = 1e3 * (exptime + latency)
        panda.DetTimePulseWidth = 1e3 * exptime
        panda.DetTimePulseN = N
        panda.TimePulsesEnable = True
        panda.ArmSingle()

        # go to the starting position
        self._set_vel(self.FAST)
        self.fast_motor.move(start - self.MARGIN)
        print('Going to X = %f ' % (start - self.MARGIN))
        while self.fast_motor.busy():
            time.sleep(self.SLEEP)
        print('...there!')

        # do a controlled movement
        vel = (abs(start - end)) / (N * (exptime + latency))
        self._set_vel(vel)
        print('Scanning at velocity %e' % vel)
        self.fast_motor.move(end)

    def _while_acquiring(self):
        print('%s: %.1f\r' % (self.fast_motor.name, self.fast_motor.user_position), end='')


class DummyPanda(object):
    PointNOut = range(100000)
    def ArmSingle(self):
        pass

