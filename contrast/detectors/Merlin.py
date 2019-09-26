from .Lima import LimaDetector
from ..environment import env

import numpy as np
import PyTango
import os

class Merlin(LimaDetector):
    def __init__(self, *args, **kwargs):
        super(Merlin, self).__init__(*args, **kwargs)
        self._hdf_path_base = 'entry_%04d/measurement/Merlin/data'

    def _initialize_det(self):
        self.energy = 10.0
        self.det.write_attribute('gain', 'HGM')
        self.det.write_attribute('depth', 'BPP24')

    @property
    def energy(self):
        return self.det.operatingEnergy
        
    @energy.setter
    def energy(self, value):
        self.det.write_attribute('operatingEnergy', value)

    def prepare(self, *args, **kwargs):
        super(Merlin, self).prepare(*args, **kwargs)
        if self.hw_trig:
            self.det.write_attribute('triggerStartType', "RISING_EDGE_TTL")
        else:
            self.det.write_attribute('triggerStartType', "INTERNAL")

