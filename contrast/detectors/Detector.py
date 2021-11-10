from ..Gadget import Gadget
from ..environment import macro
from .. import utils
import numpy as np
import time
import threading

class Detector(Gadget):
    """
    Base class representing any device which can be read out to produce
    recordable data.
    """

    def __init__(self, *args, **kwargs):
        super(Detector, self).__init__(*args, **kwargs)
        try:
            self.active = True
            self.initialize()
        except Exception as e:
            self.active = False
            print('Failed to initialize %s. Run "%s.initialize()" to try again and perhaps learn more.' % (self.name, self.name))

    @classmethod
    def get_active(cls):
        """
        Returns a DetectorGroup instance containing the currently active
        ``Detector`` instances.
        """
        return DetectorGroup(*[d for d in cls.getinstances() if (d.active and not isinstance(d, TriggerSource))])
    
    def prepare(self, acqtime, dataid, n_starts=None):
        """
        Run before acquisition, once per scan.

        :param acqtime: Acquisition time
        :type acqtime: float
        :param dataid: Data identifier, a scan id, for example.
        :param n_starts: The number of start commands we expect to issue.
        :type n_starts: int
        """
        if self.busy():
            raise Exception('%s is busy!' % self.name)
        self.acqtime = acqtime

    def arm(self):
        """
        Run before every acquisition. Arm any hardware triggered detectors.
        """
        if self.busy():
            raise Exception('%s is busy!' % self.name)

    def start(self):
        """
        Start acquisition for any software triggered detectors.
        """
        if self.busy():
            raise Exception('%s is busy!' % self.name)

    def initialize(self):
        """
        Override this method, which initializes the detector.
        """
        raise NotImplementedError

    def stop(self):
        """
        Override this method, stops the dector.
        """
        raise NotImplementedError

    def busy(self):
        """
        Override this method, returns the busy state.
        """
        raise NotImplementedError

    def read(self):
        """
        Override this method, returns the data.
        """
        raise NotImplementedError

class TriggerSource(Detector):
    """
    A TriggerSource is a device which follows the ``Detector`` API,
    but which does not produce data. It can be seen as a lightweight
    ``Detector`` subclass, where some of the methods are not mandatory.
    """
    @classmethod
    def get_active(cls):
        """
        Returns a DetectorGroup instance containing the currently active
        ``TriggerSource`` instances.
        """
        return DetectorGroup(*[d for d in cls.getinstances() if d.active])

    def stop(self):
        pass

    def busy(self):
        pass

    def read(self):
        pass

class LiveDetector(object):
    """
    Abstract class to define the interface of live detectors, which
    can run continuously with no synchronization or data capture.
    """
    def __init__(self):
        pass

    def start_live(self, acqtime=1.0):
        """
        Override this method.
        """
        raise NotImplementedError

    def stop_live(self):
        """
        Override this method.

        Should be made harmless, so that it can be run even if the
        detector is not running.
        """
        raise NotImplementedError

class SoftwareLiveDetector(LiveDetector):
    """
    Implements a software live mode, where detectors that do not provide
    a monitoring mode get started repeatedly from a background thread.
    """
    def __init__(self):
        self.thread = None
        self.stopped = False

    def start_live(self, acqtime=1.0):
        """
        Starts background acquisition.

        :param acqtime: Acquisition time.
        :type acqtime: float
        """
        if self.thread is not None: self.stop_live()
        self.stopped = False
        self.thread = threading.Thread(target=self._start, args=(acqtime,))
        self.thread.start()

    def stop_live(self):
        """
        Stops background acquisition.
        """
        # if the thread has been stopped or never started
        if self.thread is None: return
        # if the thread has died by itself for some reason
        if not self.thread.is_alive(): return
        self.stopped = True
        self.stop()
        self.thread.join()
        self.thread = None

    def _start(self, acqtime):
        while not self.stopped:
            self.prepare(acqtime, None, 1)
            self.arm()
            self.start()
            while self.busy():
                time.sleep(.05)

class TriggeredDetector(object):
    """
    Defines the API for detectors that optionally accept hardware
    triggers.
    """
    def __init__(self):
        self.hw_trig = False  # whether to arm for hw triggering
        self.hw_trig_n = 1    # the number of triggers per sw step

class BurstDetector(object):
    """
    Defines the API for detectors that optionally run in burst mode,
    so that an autonomous train of measurements is made for one
    arm/start command.

    Defines three attributes:

    * `burst_n`: the number of autonomous measurements
    * `burst_latency`: the time between measurements
    * `burst_acqtime`: an optional parameter which (if not None) overrides the value received via the prepare() method.
    """
    def __init__(self):
        # let child classes set these if they want
        if not hasattr(self, 'burst_n'):
            self.burst_n = 1
        if not hasattr(self, 'burst_latency'):
            self.burst_latency = 0.0
        if not hasattr(self, 'burst_acqtime'):
            self.burst_acqtime = None

    def prepare(self, acqtime, dataid, n_starts=None):
        self.acqtime = acqtime
        if self.burst_acqtime:
            self.acqtime = self.burst_acqtime

class DetectorGroup(object):
    """
    Collection of ``Detector`` objects to be acquired together, in a
    scan for example. Convenience class to call prepare, arm, busy etc
    in shorthand. Provides some safe measures too.
    """

    def __init__(self, *args):
        """
        :param ``*args``: Sequence of ``Detector`` instances
        """
        self.detectors = list()
        for arg in args:
            self.detectors.append(arg)

    def prepare(self, acqtime, dataid, n_starts, trials=1, trial_delay=1.):
        """
        Runs ``prepare`` on each of the constituent ``Detector``
        instances.
        """
        for d in self:
            ok = False
            tried = 0
            while not ok:
                try:
                    d.prepare(acqtime, dataid, n_starts)
                    ok = True
                except (AssertionError, NotImplementedError):
                    raise
                except:
                    tried += 1
                    print('*** problem calling prepare() on %s, trying again in %f s...' % (d.name, trial_delay))
                    time.sleep(trial_delay)
                    if tried == trials:
                        raise

    def arm(self):
        """
        Arms all constituent devices.
        """
        for d in self:
            d.arm()

    def start(self, trials=1, trial_delay=1.):
        """
        Starts all constituent devices.
        """
        for d in self:
            ok = False
            tried = 0
            while not ok:
                try:
                    d.start()
                    ok = True
                except AssertionError:
                    raise
                except:
                    tried += 1
                    print('*** problem calling start() on %s, trying again in %f s...' % (d.name, trial_delay))
                    time.sleep(trial_delay)
                    if tried == trials:
                        raise

    def stop(self):
        """
        Stops all constituent devices.
        """
        for d in self:
            d.stop()

    def busy(self):
        """
        Checks if one or more of the  constituent devices is busy.
        """
        for d in self:
            if d.busy(): return True
        return False

    def __iter__(self):
        return self.detectors.__iter__()

    def __len__(self):
        return self.detectors.__len__()

    def __add__(self, other):
        return DetectorGroup(*self.detectors, *other.detectors)

@macro
class LsDet(object):
    """
    List available detectors.
    """
    def run(self):
        dct = {}
        for d in Detector.getinstances():
            if isinstance(d, TriggerSource):
                continue
            name = ('* ' + d.name) if d.active else ('  ' + d.name)
            try:
            # rough sense of how each detector is doing
                if d.busy():
                    name += ' (busy)'
            except:
                name += '  (not responding)'

            dct[name] = d.__class__
        print(utils.dict_to_table(dct, titles=('  name', 'class')))

@macro
class LsTrig(object):
    """
    List available trigger sources.
    """
    def run(self):
        dct = {}
        for d in TriggerSource.getinstances():
            name = ('* ' + d.name) if d.active else ('  ' + d.name)
            try:
            # rough sense of how each detector is doing
                if d.busy():
                    name += ' (busy)'
            except:
                name += '  (not responding)'
            
            dct[name] = d.__class__
        print(utils.dict_to_table(dct, titles=('  name', 'class')))

@macro
class StartLive(object):
    """
    Starts software live mode on listed eligible detectors. If none
    are listed, all active and eligible detectors are started. ::

        startlive [<det1> ... <detN> <exposure time>]
    """
    def __init__(self, *args):
        try:
            self.exptime = float(args[-1])
            self.dets = args[:-1]
        except (TypeError, IndexError):
            self.exptime = .1
            self.dets = args
        if not self.dets:
            self.dets = [d for d in Detector.get_active() if isinstance(d, LiveDetector)]

    def run(self):
        for d in self.dets:
            if isinstance(d, LiveDetector):
                d.start_live(float(self.exptime))
            else:
                print('%s is not a LiveDetector' % d.name)

@macro
class StopLive(object):
    """
    Stops software live mode on listed eligible detectors. If
    no arguments are given, all active live detectors are
    stopped. ::

        stoplive [<det1> ... <detN>]
    """
    def __init__(self, *args):
        if args:
            self.dets = args
        else:
            self.dets = [d for d in Detector.get_active() if isinstance(d, LiveDetector)]

    def run(self):
        for d in self.dets:
            if isinstance(d, LiveDetector):
                d.stop_live()
            else:
                print('%s is not a LiveDetector' % d.name)

@macro
class Deactivate(object):
    """
    Deactivates all detectors or those specified. ::

        deactivate [<det1> ... <detN>]
    """
    def __init__(self, *args):
        if args:
            self.dets = args
        else:
            self.dets = Detector.getinstances()

    def run(self):
        for d in self.dets:
            d.active = False

@macro
class Activate(object):
    """
    Activates all detectors or those specified. ::

        activate [<det1> ... <detN>]
    """
    def __init__(self, *args):
        if args:
            self.dets = args
        else:
            self.dets = Detector.getinstances()

    def run(self):
        for d in self.dets:
            d.active = True

