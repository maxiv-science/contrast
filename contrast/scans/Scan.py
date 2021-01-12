import time
import datetime
import numpy as np
from ..environment import macro, env
from ..recorders import active_recorders, RecorderHeader, RecorderFooter
from ..detectors import Detector, TriggerSource
from ..utils import SpecTable
from collections import OrderedDict
import sys

class SoftwareScan(object):
    """
    Base class for the normal sardana-style software-controlled scan.
    Respects the availability and deadlines managed by env.scheduler,
    honours env.shapshot, and acts on all active detectors, trigger
    sources, and recorders.
    """

    dict_print_length = 5
    str_print_length = 12

    def __init__(self, exposuretime):
        """
        The constructor should parse the parameters of the derived
        macro.

        :param exposuretime: Exposure time to pass on to detectors etc.
        :type exposuretime: float
        """
        self.motors = []   # list of motors, to be filled by subclass
        self.exposuretime = exposuretime
        self.scannr = env.nextScanID
        self.n_positions = None
        self.print_progress = True
        env.nextScanID += 1

    def output(self, i, dct):
        # ignore dicts that are too long
        for k, v in dct.items():
            if type(v) == dict and len(v) > self.dict_print_length:
                dct[k] = {'...':'...'}
        dct['     #'] = i
        dct.move_to_end('     #', last=False)
        if i == 0:
            self.table = SpecTable()
            self.table.max_str_len = self.str_print_length
            header = self.table.header_lines(dct)
            print('\n'+header)
            print('-'*len(header.split('\n')[-1]))
        print(self.table.fill_line(dct))
        if self.n_positions and self.print_progress:
            timeleft = str(datetime.timedelta(seconds=(self.n_positions-i)*dct['dt']/(i+1))).split('.')[0]
            print('Time left: %s\r' % timeleft, end='')

    def _calc_time_needed(self):
        """
        Estimates the time needed for performing the next acquisition.
        This can be done based on the input parameters, or on the timing
        of previous points.
        """
        return self.exposuretime * 5 + 5

    def _before_scan(self):
        """
        Placeholder method for users to hook actions onto scan classes
        after import. For example opening a shutter::

            def pre_scan_stuff(slf):
                print("Maybe open a shutter here?")
            SoftwareScan._before_scan = pre_scan_stuff
        """
        pass

    def _after_scan(self):
        """
        Placeholder method for users to hook actions onto scan classes
        after import, see ``_before_scan``.
        """
        pass

    def _before_move(self):
        """
        Gets called for each step, and can be used for example to check
        that the instrument is ready for the next acquisition, that
        there is beam in the machine, etc.
        """

        # Example implementation of topup avoidance
        time_needed = self._calc_time_needed()
        limit = env.scheduler.limit
        enough_time = time_needed < limit if limit else True
        ready = env.scheduler.ready
        found_not_ready = False
        try:
            while not ready or not enough_time:
                if not enough_time:
                    print('not enough time to complete this measurement so waiting, press ctrl-c to ignore from now on...')
                else:
                    if not found_not_ready:
                        print('Waiting for beamline to become available, press ctrl-c to ignore from now on...')
                        found_not_ready = True
                    else:
                        print('.', end='')
                        sys.stdout.flush()
                time.sleep(1.)
                limit = env.scheduler.limit
                enough_time = time_needed < limit if limit else True
                ready = env.scheduler.ready
        except KeyboardInterrupt:
            env.scheduler.disabled = True

    def _before_arm(self):
        """
        Gets called for each step. See ``_before_move``.
        """
        pass

    def _while_acquiring(self):
        """
        Gets called repeatedly while the detectors detect. Useful for
        printing a progress bar, for example.
        """
        pass

    def _before_start(self):
        """
        Gets called for each step. See ``_before_move``.
        """
        pass

    def run(self):
        """
        This is the main acquisition loop where interaction with motors,
        detectors and other ``Gadget`` objects happens.
        """
        self._before_scan()
        print('\nScan #%d starting at %s' % (self.scannr, time.asctime()))
        positions = self._generate_positions()
        # find and prepare the detectors
        det_group = Detector.get_active()
        trg_group = TriggerSource.get_active()
        group = det_group + trg_group
        if group.busy():
            print('These gadgets are busy: %s' % (', '.join([d.name for d in group if d.busy()])))
            return
        group.prepare(self.exposuretime, self.scannr, self.n_positions, trials=100)
        t0 = time.time()
        # send a header to the recorders
        snap = env.snapshot.capture()
        for r in active_recorders():
            r.queue.put(RecorderHeader(scannr=self.scannr, 
                                       status='started',
                                       path=env.paths.directory,
                                       snapshot=snap, 
                                       description=self._command))
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
                group.start(trials=100)
                while det_group.busy():
                    self._while_acquiring()
                    time.sleep(.01)
                # read detectors and motors
                dt = time.time() - t0
                dct = OrderedDict()
                for m in self.motors:
                    dct[m.name] = m.position()
                for d in det_group:
                    dct[d.name] = d.read()
                dct['dt'] = dt
                # pass data to recorders
                for r in active_recorders():
                    r.queue.put(dct)
                # print spec-style info
                self.output(i, dct.copy())
            print('\nScan #%d ending at %s' % (self.scannr, time.asctime()))

            # tell the recorders that the scan is over
            for r in active_recorders():
                r.queue.put(RecorderFooter(scannr=self.scannr,
                                           status='finished',
                                           path=env.paths.directory,
                                           snapshot=snap, 
                                           description=self._command))

        except KeyboardInterrupt:
            group.stop()
            print('\nScan #%d cancelled at %s' % (self.scannr, time.asctime()))

            # tell the recorders that the scan was interrupted
            for r in active_recorders():
                r.queue.put(RecorderFooter(scannr=self.scannr,
                                           status='interrupted',
                                           path=env.paths.directory,
                                           snapshot=snap, 
                                           description=self._command))
        except:
            self._after_scan()
            raise

        # do any user-defined cleanup actions
        self._after_scan()

        
    def _generate_positions(self):
        """
        *Override this method.* Function or generator which returns or
        yields an iterable of dicts, ::

            {motorA.name: posA, motorB.name: posB, ...}
        """
        raise NotImplementedError

@macro
class LoopScan(SoftwareScan):
    """
    A software scan with no motor movements. Number of exposures is
    <intervals> + 1, for consistency with ascan, dscan etc. ::

        loopscan <intervals> <exp_time>
    """
    def __init__(self, intervals, exposuretime=1.0):
        super(LoopScan, self).__init__(float(exposuretime))
        self.intervals = intervals
        self.n_positions = intervals + 1
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
    is 1.0. ::

        ct [<exp_time>]
    """
    def __init__(self, exp_time=1, print_nd=True):
        self.exposuretime = float(exp_time)

    def _before_ct(self):
        """
        Placeholder method for users to hook actions onto scan classes after import.
        """
        pass

    def _after_ct(self):
        """
        Placeholder method for users to hook actions onto scan classes after import.
        """
        pass

    def run(self):
        self._before_ct()
        # find and prepare the detectors
        det_group = Detector.get_active()
        group = det_group + TriggerSource.get_active()
        group.prepare(self.exposuretime, dataid=None, n_starts=1)
        # arm and start detectors
        group.arm()
        group.start()
        try:
            while group.busy():
                time.sleep(.01)
        except KeyboardInterrupt:
            group.stop()
        # read detectors and motors
        dct = {}
        for d in det_group:
            dct[d.name] = d.read()
        # print results
        for key, val in dct.items():
            print(key, ':', val)
        self._after_ct()
