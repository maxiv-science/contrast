import os
import sys
assert sys.version_info.major == 3, 'Use ipython3 instead.'

from . import recorders
from . import detectors
from . import motors
from . import scans
from . import Gadget
from . import utils
from . import environment

def wisdom():
    """
    Prints the current meaning of the acronym Contrast.
    """
    import random
    from .abbreviations import abbrv
    ind = random.randint(0, len(abbrv)-1)
    print('\nWelcome to contrast,\n')
    print('   "%s"'%abbrv[ind])

