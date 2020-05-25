from .Detector import Detector
try:
    import PyTango
except ModuleNotFoundError:
    pass
import numpy as np

class Keysight2985(Detector):
    """
    Interface to the Keysight electrometer at
    https://gitlab.maxiv.lu.se/kits-maxiv/dev-maxiv-keysight2980
    """
    def __init__(self, name=None, device=None):
        self.dev_name = device
        super().__init__(name=name)

    def initialize(self):
        self.dev = PyTango.DeviceProxy(self.dev_name)
        self.dev.init()
        
    def prepare(self, acqtime, dataid, n_starts):
        self.dev.write_attribute('integration_time', acqtime)
        self.dev.InputOn()
        if self.busy():
            raise Exception('%s is busy!' % self.name)

    def arm(self):
        pass

    def start(self):
        self.dev.Measure()

    def stop(self):
        pass

    def busy(self):
        return (self.dev.State() == PyTango.DevState.RUNNING)

    def read(self):
        return self.dev.read_attribute('measured_current').value

    @property
    def current_range(self):
        return self.dev.current_range

