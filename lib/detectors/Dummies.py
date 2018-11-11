from .Detector import Detector, LiveDetector, Link

import time
import numpy as np
import h5py

class DummyDetector(Detector, LiveDetector):
    def __init__(self, name=None):
        Detector.__init__(self, name=name)
        LiveDetector.__init__(self)

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

class Dummy1dDetector(DummyDetector):
    def start(self):
        super(Dummy1dDetector, self).start()
        try:
            self.val = np.random.rand(100) * self.acqtime
            self._started = time.time()
        except AttributeError:
            raise Exception('Detector not prepared!')

class DummyWritingDetector(DummyDetector):
    def prepare(self, acqtime, dataid):
        super(DummyWritingDetector, self).prepare(acqtime, dataid)
        if dataid is None:
            self.filename_base = None
        else:
            self.filename_base = '/tmp/Dummy_scan_%03d_image_%%03d' % dataid
            self.next_image = -1

    def start(self):
        super(DummyWritingDetector, self).start()
        if self.filename_base is None:
            self.latest_link = None
        else:
            self.next_image += 1
            filename = self.filename_base % self.next_image
            datapath = 'entry/measurement/data'
            with h5py.File(filename, 'w') as fp:
                fp[datapath] = np.arange(195*487).reshape((195, 487))
            self.latest_link = Link(filename, datapath)

    def read(self):
        return self.latest_link
