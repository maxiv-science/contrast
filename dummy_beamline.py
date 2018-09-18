# need this main guard here because Process.start() (so our recorders)
# import __main__, and we don't want the subprocess to start new sub-
# processes etc.
if __name__=='__main__':

    from src.motors import DummyMotor
    from src.scans import *
    from src.detectors import DummyDetector, DetectorGroup, Dummy1dDetector
    from src.environment import env
    from src.recorders import Hdf5Recorder

    import os

    env.userLevel = 1 # we're not experts!

    samx = DummyMotor('samx')
    samy = DummyMotor('samy')
    gap = DummyMotor('gap', userlevel=5)

    det1 = DummyDetector('det1')
    det2 = DummyDetector('det2')
    det3 = Dummy1dDetector('det3')

    detgrp = DetectorGroup('detgrp', det1, det2, det3)

    env.currentDetectorGroup = detgrp

    try:
        os.remove('/tmp/data.h5')
    except FileNotFoundError:
        pass
    rec = Hdf5Recorder('/tmp/data.h5')
    rec.start()
