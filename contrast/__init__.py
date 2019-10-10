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
    import random
    dirpath = os.path.dirname(os.path.realpath(__file__))
    with open(dirpath+'/abbreviations') as fp:
        abbrvs = fp.read().strip().split('\n')
    ind = random.randint(0, len(abbrvs)-1)
    print('\nWelcome to contrast,\n')
    print('   "%s"'%abbrvs[ind])
