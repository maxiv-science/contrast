from ..Gadget import Gadget
from ..environment import macro
from .. import utils
import numpy as np
import time
import threading
from h5py import ExternalLink

class Detector(Gadget):
    """
    Base class representing any device which can be read out to produce
    recordable data.
    """

    def __init__(self, *args, **kwargs):
        super(Detector, self).__init__(*args, **kwargs)
        self.active = True
        self.initialize()

    @classmethod
    def get_active_detectors(cls):
        """
        Returns a DetectorGroup instance containing the currently active
        detectors.
        """
        return DetectorGroup(*[d for d in cls.getinstances() if d.active])
    
    def prepare(self, acqtime, dataid):
        """
        Run before acquisition, once per scan.
            acqtime: exposure time for which to prepare
            dataid:  some way of identifying the data to
                     collected, useful for detectors that
                     write their own data files.
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
        Mandatory method for initializing a detector.
        """
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def busy(self):
        raise NotImplementedError

    def read(self):
        raise NotImplementedError

class LiveDetector(object):
    """
    Implements software live mode, i e making repeated acquisitions to
    make a detector run continuously with no synchronization or data
    capture.
    """
    def __init__(self):
        self.thread = None
        self.stopped = False

    def start_live(self, acqtime=1.0):
        self.thread = threading.Thread(target=self._start, args=(acqtime,))
        self.thread.start()

    def stop_live(self):
        if not self.thread: return
        self.stopped = True
        self.thread.join()

    def _start(self, acqtime):
        self.stopped = False
        self.prepare(acqtime, None)
        while not self.stopped:
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
        self.hw_trig = False
        self.hw_trig_n = 1

class DetectorGroup(object):
    """
    Collection of Detector objects to be acquired together, in a scan
    for example. Convenience class to call prepare, arm, busy etc
    in shorthand.
    """

    def __init__(self, *args):
        self.detectors = list()
        for arg in args:
            self.detectors.append(arg)

    def prepare(self, acqtime, dataid):
        for d in self:
            d.prepare(acqtime, dataid)

    def arm(self):
        for d in self:
            d.arm()

    def start(self):
        for d in self:
            d.start()

    def stop(self):
        for d in self:
            d.stop()

    def busy(self):
        for d in self:
            if d.busy(): return True
        return False

    def __iter__(self):
        return self.detectors.__iter__()

    def __len__(self):
        return self.detectors.__len__()

class Link(ExternalLink):
    """
    Some detectors write their own data to disk. When that happens,
    return data should be a link to where the actual data was saved.
    This class represents such links and is a simple wrapper around
    h5py.ExternalLink.
    """
    def __str__(self):
        return '<link>'

@macro
class LsDet(object):
    """
    List available detectors.
    """
    def run(self):
        dct = {}
        for d in Detector.getinstances():
            name = ('* ' + d.name) if d.active else ('  ' + d.name)
            dct[name] = d.__class__
        print(utils.dict_to_table(dct, titles=('  name', 'class')))
