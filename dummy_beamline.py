"""
Sets up a mock beamline with dummy motors and detectors.
"""

# need this main guard here because Process.start() (so our recorders)
# import __main__, and we don't want the subprocess to start new sub-
# processes etc.
if __name__=='__main__':

    from lib.motors import DummyMotor
    from lib.scans import *
    from lib.detectors import DummyDetector, DetectorGroup, Dummy1dDetector
    from lib.environment import env
    from lib.recorders import Hdf5Recorder

    import os

    env.userLevel = 1 # we're not experts!

    samx = DummyMotor('samx')
    samx.limits = (0, 10)

    samy = DummyMotor('samy')
    samy.limits = (-5, 5)

    gap = DummyMotor('gap', userlevel=5)
    gap._format = '%8f'

    det1 = DummyDetector('det1')
    det2 = DummyDetector('det2')
    det3 = Dummy1dDetector('det3')

    detgrp = DetectorGroup('detgrp', det1, det2, det3)

    env.currentDetectorGroup = detgrp

    try:
        os.remove('/tmp/data.h5')
    except FileNotFoundError:
        pass
    h5rec = Hdf5Recorder('/tmp/data.h5', name='h5rec')
    h5rec.start()
