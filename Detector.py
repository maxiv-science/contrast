from Gadget import Gadget
from Environment import macro
import utils
import numpy as np
import time

print(__name__)

class Detector(Gadget):
    """
    Base class representing any device which can be read out to produce
    recordable data.
    """
    
    def prepare(self, acqtime):
        if self.busy():
            raise Exception('%s is busy!' % self.name)
        self.acqtime = acqtime

    def start(self):
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
    def startLive(self, acqtime):
        pass

    def stopLive(self):
        pass

class DetectorGroup(Gadget):
    """
    Collection of Detector objects to be acquired together, in a scan
    for example.
    """

    def __init__(self, name, *args):
        super(DetectorGroup, self).__init__(name)
        self.detectors = list()
        self.append(args)

    def prepare(self, acqtime):
        for d in self:
            d.prepare(acqtime)

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


class DummyDetector(Detector, LiveDetector):
    def start(self):
        super(DummyDetector, self).start()
        try:
            self.val = np.random.rand() * self.acqtime
            self._started = time.time()
        except AttributeError:
            raise Exception('Detector not prepared!')

    def stop(self):
        try:
            self._started = time.time() - self.acqtime
        except AttributeError:
            return

    def busy(self):
        try:
            return time.time() < self._started + self.acqtime
        except AttributeError:
            return False

    def read(self):
        try:
            return self.val
        except AttributeError:
            raise Exception('Detector not started!')

class DummyWritingDetector(DummyDetector):
    def read(self):
        try:
            return Link('/home/alex/files/images/scan.hdf5')
        except AttributeError:
            raise Exception('Detector not started!')

class Link(object):
    """
    Some detectors write their own data to disk. When that happens,
    return data should be a link to where the actual data was saved.
    This class represents such links.
    """
    def __init__(self, target=None):
        self.target = target
    def __str__(self):
        return '<%s>' % self.target

@macro
class LsDet(object):
    def run(self):
        dct = {d.name: d.__class__ for d in Detector.getinstances()}
        print(utils.dict_to_table(dct, titles=('name', 'class')))

@macro
class LsGrp(object):
    def run(self):
        dct = {d.name: d.__class__ for d in DetectorGroup.getinstances()}
        print(utils.dict_to_table(dct, titles=('name', 'class')))
