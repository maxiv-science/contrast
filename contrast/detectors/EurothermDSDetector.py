"""
Provides a Detector interface to the EUrothermDS Tango Device

for 20231270 Carbone (starting 2024/05/21)
"""

from .Detector import Detector
import PyTango

class EuroThermDSDetector(Detector):
    """
    Detector interface to  EurothermDS tango device, reading the
    'Temperature_PV1' value.
    """
    def __init__(self, name, device, scaling_factor=10.):
        super(EuroThermDSDetector, self).__init__(name=name)
        self.proxy = PyTango.DeviceProxy(device)
        self.attribute = 'Temperature_PV1'
        self.scaling_factor = float(scaling_factor)

    def initialize(self):
        pass

    def start(self):
        super(EuroThermDSDetector, self).start()

    def stop(self):
        pass

    def busy(self):
        return False

    def read(self):
        return self.proxy.read_attribute(self.attribute).value / self.scaling_factor
