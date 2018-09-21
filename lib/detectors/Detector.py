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
        while not self.stopped:
            self.prepare(acqtime, None)
            self.start()
            while self.busy():
                time.sleep(.05)

class DetectorGroup(Gadget):
    """
    Collection of Detector objects to be acquired together, in a scan
    for example.
    """

    def __init__(self, name, *args):
        super(DetectorGroup, self).__init__(name)
        self.detectors = list()
        self.append(args)

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

    def append(self, obj):
        """
        Append a single detector, another DetectorGroup, or any iterable
        containing detectors.
        """
        try:
            for d in obj:
                self.append(d)
        except TypeError:
            assert isinstance(obj, Detector), 'DetectorGroup can only contain Detectors!'
            if obj not in self.detectors:
                self.detectors.append(obj)

    def __str__(self):
        names = [d.name for d in self]
        classes = [d.__class__ for d in self]
        dct = {n: c for n, c in zip(names, classes)}
        return utils.dict_to_table(dct, titles=('name', 'class'))

class Link(object):
    """
    Some detectors write their own data to disk. When that happens,
    return data should be a link to where the actual data was saved.
    This class represents such links.
    """
    def __init__(self, target=None):
        self.target = target
    def __str__(self):
        return '<link>'

@macro
class LsDet(object):
    """
    List available detectors.
    """
    def run(self):
        dct = {d.name: d.__class__ for d in Detector.getinstances()}
        print(utils.dict_to_table(dct, titles=('name', 'class')))

@macro
class LsGrp(object):
    """
    List detector groups.
    """
    def run(self):
        dct = {d.name: d.__class__ for d in DetectorGroup.getinstances()}
        print(utils.dict_to_table(dct, titles=('name', 'class')))
