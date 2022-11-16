"""
Provides a Detector interface to Tango attributes, so that anything
can be monitored during scans.
"""

from .Detector import Detector
import PyTango

class TangoAttributeDetector(Detector):
    """
    Detector interface to Tango attributes, so that anything can be
    monitored during scans. These detectors simply take snapshots
    of Tango attributes and are never busy.
    """
    def __init__(self, name, device, attribute):
        super(TangoAttributeDetector, self).__init__(name=name)
        self.proxy = PyTango.DeviceProxy(device)
        self.attribute = attribute

    def initialize(self):
        pass

    def start(self):
        super(TangoAttributeDetector, self).start()

    def stop(self):
        pass

    def busy(self):
        return False

    def read(self):
        return self.proxy.read_attribute(self.attribute).value
