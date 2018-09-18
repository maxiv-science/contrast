from .Detector import Detector, LiveDetector

import time
import numpy as np

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

class Dummy1dDetector(DummyDetector):
    def start(self):
        super(Dummy1dDetector, self).start()
        try:
            self.val = np.random.rand(100) * self.acqtime
            self._started = time.time()
        except AttributeError:
            raise Exception('Detector not prepared!')

class DummyWritingDetector(DummyDetector):
    def read(self):
        try:
            return Link('/home/alex/files/images/scan.hdf5')
        except AttributeError:
            raise Exception('Detector not started!')
