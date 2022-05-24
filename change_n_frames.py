import sys
from contrast.detectors.Andor3 import Andor3, AndorSofti
from contrast.detectors.PandaBoxSofti import PandaBoxSoftiPtycho

n_frames = int(sys.argv[1])
del andor
del panda0
andor = AndorSofti(device='B318A-EA01/dia/andor-zyla-01', name='andor', shutter=shutter0, frames_n=n_frames)
panda0 = PandaBoxSoftiPtycho(name='panda0', host='b-softimax-panda-0', frames_n=2*n_frames)