"""
Sets up a some actual nanomax hardware.
"""

# need this main guard here because Process.start() (so our recorders)
# import __main__, and we don't want the subprocess to start new sub-
# processes etc.
if __name__=='__main__':

    import contrast
    from contrast.environment import env, runCommand
    from contrast.environment.data import PathFixer
    from contrast.recorders import Hdf5Recorder, StreamRecorder
    from contrast.motors import DummyMotor, MotorMemorizer
    from contrast.motors.LC400 import LC400Motor
    from contrast.detectors.LC400Buffer import LC400Buffer
    from contrast.motors.TangoMotor import TangoMotor
    # from contrast.detectors.Ni6602 import Ni6602CounterCard
    # from contrast.detectors.AdLink import AdLinkAnalogInput
    from contrast.detectors import DummyDetector, Dummy1dDetector, DummyWritingDetector, DummyWritingDetector2
    from contrast.detectors import Detector, TriggeredDetector
    from contrast.detectors.DG645 import StanfordTriggerSource
    from contrast.detectors.PandaBox import PandaBox
    # from nanomax_beamline_macros import *
    from NpointFlyscan import NpointFlyscan
    #from macro_attenuate import *
    from contrast.scans import SoftwareScan, Ct
    import os
    
    env.userLevel = 4
    # chosen these levels here:
    # 1 - simple user
    # 2 - power user
    # 3 - optics
    # 4 - potentially dangerous

    # sample piezos
    sx = LC400Motor(device='NPOINTLC400b/USB/1', axis=2, name='sx', scaling=-1.0, dial_limits=(-101,101))
    sy = LC400Motor(device='NPOINTLC400b/USB/1', axis=3, name='sy', dial_limits=(-51,51))
    sz = LC400Motor(device='NPOINTLC400b/USB/1', axis=1, name='sz', scaling=-1.0, dial_limits=(-101,101))

    # buffered position detector
    npoint_buff = LC400Buffer(device='lc400scancontrol/test/1', name='npoint_buff', xaxis=2, yaxis=3, zaxis=1)
    npoint_buff.active = False # this can be switched on from flyscanning macros when needed, although it does no harm.

    # some dummy motors
    dummy1 = DummyMotor(name='dummy1', userlevel=2)
    dummy2 = DummyMotor(name='dummy2', userlevel=2)

    # The delay generator as a software source for hardware triggers
    stanford = StanfordTriggerSource(name='stanford', device_name='test/delay/dly-01')

    # Tha PandABox is a detector/counter for TTLs and encoders, and a trigger source
    panda = PandaBox(name='panda', host='172.16.123.9')
    panda.active = True
    panda.initialize()

    # Detectors
    #ni = Ni6602CounterCard(name='ni', device='B303A/CTL/NI6602-01')
    det1 = DummyDetector(name='det1')
    det2 = DummyWritingDetector(name='det2')
    det3 = Dummy1dDetector(name='det3')

    det1.active = True
    det2.active = True
    det3.active = True


    # the environment keeps track of where to write data
    env.paths = PathFixer()
    env.paths.directory = '/tmp/contrast'

    # an hdf5 recorder
    h5rec = Hdf5Recorder(name='h5rec')
    h5rec.start()

    # a zmq recorder
    zmqrec = StreamRecorder(name='zmqrec')
    zmqrec.start() # removed for now

    # add a memorizer so the motors keep their user positions and limits after a restart
    # note that this will overwrite the dial positions set above! delete the file to generate it again.
    memorizer = MotorMemorizer(name='memorizer', filepath='/tmp/nanomotionlab_memorizer')

    
    # define pre- and post-scan actions, per scan base class
    import PyTango
    import time
    def pre_scan_stuff(slf):
        runCommand('stoplive')
    def post_scan_stuff(slf):
        pass

    SoftwareScan._before_scan = pre_scan_stuff
    SoftwareScan._after_scan = post_scan_stuff
    Ct._before_ct = pre_scan_stuff
    Ct._after_ct = post_scan_stuff

    contrast.wisdom()
    print("* Welcome to the NanoMotionLab *")
