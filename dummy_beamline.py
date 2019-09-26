"""
Sets up a mock beamline with dummy motors and detectors.
"""

# need this main guard here because Process.start() (so our recorders)
# import __main__, and we don't want the subprocess to start new sub-
# processes etc.
if __name__=='__main__':

    from lib.motors import DummyMotor, MotorMemorizer, ExamplePseudoMotor
    from lib.scans import *
    from lib.detectors import DummyDetector, Dummy1dDetector, DummyWritingDetector
    from lib.environment import env
    from lib.recorders import Hdf5Recorder

    import os

    env.userLevel = 1 # we're not experts!

    samx = DummyMotor(name='samx')
    samx.dial_limits = (0, 10)

    samy = DummyMotor(name='samy')
    samy.dial_limits = (-5, 5)

    gap = DummyMotor(name='gap', userlevel=5, user_format='%.5f')

    diff = ExamplePseudoMotor([samx, samy], name='diff')

    det1 = DummyDetector(name='det1')
    det2 = DummyWritingDetector(name='det2')
    det3 = Dummy1dDetector(name='det3')

    env.paths.directory = '/tmp'

    # remove old files
    files = os.listdir(env.paths.directory)
    for file in files:
        if file.endswith(".h5"):
            os.remove(os.path.join(env.paths.directory, file))

    # the Hdf5Recorder later gets its path from the env object
    h5rec = Hdf5Recorder(name='h5rec')
    h5rec.start()

    # this MotorMemorizer keeps track of motor user positions and
    # limits, and dumps this to file when they are changed.
    memorizer = MotorMemorizer(name='memorizer', filepath='/tmp/.dummy_beamline_motors')
