from .Lima import LimaDetector
from ..environment import env

import numpy as np
import PyTango
import os

class Pilatus(LimaDetector):
    def __init__(self, *args, **kwargs):
        super(Pilatus, self).__init__(*args, **kwargs)
        self._hdf_path_base = 'entry_%04d/measurement/Pilatus/data'

    def _initialize_det(self):
        self.energy = 10.0

    @property
    def energy(self):
        return self.det.energy_threshold
        
    @energy.setter
    def energy(self, value):
        if value < 4.5 or value > 36:
            raise ValueError('Requested value is outside the Pilatus range of 4.5-36 keV')
        self.det.write_attribute('energy_threshold', value)

