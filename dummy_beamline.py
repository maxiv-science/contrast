"""
Sets up a mock beamline with dummy motors and detectors.
"""

# need this main guard here because Process.start() (so our recorders)
# import __main__, and we don't want the subprocess to start new sub-
# processes etc.
if __name__=='__main__':

    from lib.motors import DummyMotor
    from lib.scans import *
    from lib.detectors import DummyDetector, Dummy1dDetector, DummyWritingDetector
    from lib.environment import env
    from lib.recorders import Hdf5Recorder
    from lib.scheduling import DummyInjectionScheduler

    import os

    env.userLevel = 1 # we're not experts!

    samx = DummyMotor('samx')
    samx.limits = (0, 10)

    samy = DummyMotor('samy')
    samy.limits = (-5, 5)

    gap = DummyMotor('gap', userlevel=5)
    gap._format = '%8f'

    det1 = DummyDetector('det1')
    det2 = DummyWritingDetector('det2')
    det3 = Dummy1dDetector('det3')

    env.paths.directory = '/tmp'

    # remove old files
    files = os.listdir(env.paths.directory)
    for file in files:
        if file.endswith(".h5"):
            os.remove(os.path.join(env.paths.directory, file))

    # the Hdf5Recorder later gets its path from the env object
    h5rec = Hdf5Recorder(name='h5rec')
    h5rec.start()

    # fake top-up scheduling
    env.scheduler = DummyInjectionScheduler()
