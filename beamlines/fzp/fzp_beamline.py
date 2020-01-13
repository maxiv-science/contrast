"""
Sets up a some actual nanomax hardware.
"""

# need this main guard here because Process.start() (so our recorders)
# import __main__, and we don't want the subprocess to start new sub-
# processes etc.
if __name__=='__main__':

    import contrast
    from contrast.environment import env, runCommand
    from contrast.environment.data import SdmPathFixer
    from contrast.recorders import Hdf5Recorder, StreamRecorder
    from contrast.motors import DummyMotor, MotorMemorizer
    from contrast.motors.TangoMotor import TangoMotor
    from contrast.motors.SmaractMotor import SmaractLinearMotor
    from contrast.detectors.Pilatus import Pilatus
    from contrast.detectors.Ni6602 import Ni6602CounterCard
    from contrast.detectors.AdLink import AdLinkAnalogInput
    from contrast.detectors import Detector
    from contrast.detectors.DG645 import StanfordTriggerSource
    from nanomax_beamline_macros import *
    from macro_attenuate import *
    from contrast.scans import SoftwareScan, Ct
    import os

    env.userLevel = 1
    # chosen these levels here:
    # 1 - simple user
    # 2 - power user
    # 3 - optics
    # 4 - potentially dangerous

    # fzp motors
    fzpx = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-06', axis=0, name='fzpx', userlevel=1)
    fzpy = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-06', axis=1, name='fzpy', userlevel=1)
    fzpz = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-06', axis=2, name='fzpz', userlevel=1)
    csx = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-06', axis=3, name='csx', userlevel=1)
    csy = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-06', axis=4, name='csy', userlevel=1)
    csz = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-06', axis=5, name='csz', userlevel=1)
    osax = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-06', axis=6, name='osax', userlevel=1)
    osay = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-06', axis=7, name='osay', userlevel=1)
    osaz = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-06', axis=8, name='osaz', userlevel=1)
    r0 = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-06', axis=17, name='r0', userlevel=1)

    # some dummy motors
    dummy1 = DummyMotor(name='dummy1', userlevel=2)
    dummy2 = DummyMotor(name='dummy2', userlevel=2)


    # the environment keeps track of where to write data
    env.paths.directory = '/tmp'

    # an hdf5 recorder
    h5rec = Hdf5Recorder(name='h5rec')
    h5rec.start()

    # add a memorizer so the motors keep their user positions and limits after a restart
    # note that this will overwrite the dial positions set above! delete the file to generate it again.
    memorizer = MotorMemorizer(name='memorizer', filepath='/data/visitors/nanomax/common/sw/beamlines/fzp/.memorizer')

    # define pre- and post-scan actions, per scan base class
    import PyTango
    import time
    #shutter = PyTango.DeviceProxy('B303A-O/PSS/BS-01')
    def pre_scan_stuff(slf):
        #shutter.open()
        # runCommand('fsopen')
        time.sleep(1)
        # runCommand('stoplive')
    def post_scan_stuff(slf):
        time.sleep(1)
        #shutter.close()
        #runCommand('fsclose')

    SoftwareScan._before_scan = pre_scan_stuff
    SoftwareScan._after_scan = post_scan_stuff
    Ct._before_ct = pre_scan_stuff
    Ct._after_ct = post_scan_stuff

    contrast.wisdom()
