# need this main guard here because Process.start() (so our recorders)
# import __main__, and we don't want the subprocess to start new sub-
# processes etc.
if __name__=='__main__':

    from src.motors import DummyMotor
    from src.scans import *
    from src.detectors import DummyDetector, DetectorGroup
    from src.environment import env
    from src.recorders import PlotRecorder, DummyRecorder

    print(__name__)

    samx=DummyMotor('samx')
    samy=DummyMotor('samy')
    det1 = DummyDetector('det1')
    det2 = DummyDetector('det2')

    detgrp = DetectorGroup('detgrp', det1, det2)

    env.currentDetectorGroup = detgrp

    #rec = PlotRecorder('samx', 'det1')
    #rec = DummyRecorder('rec')
    #rec.start()
