from .Lima import LimaDetector
from ..environment import env

import numpy as np
import PyTango
import os

class Xspress3(LimaDetector):
    EXT_TRG_MODE = "EXTERNAL_GATE"

    def __init__(self, *args, **kwargs):
        super(Xspress3, self).__init__(*args, **kwargs)
        self._hdf_path_base = 'entry_%04d/measurement/xspress3/data'

