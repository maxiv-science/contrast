"""
The imaging endstation at NanoMAX.
"""

# need this main guard here because Process.start() (so our recorders)
# import __main__, and we don't want the subprocess to start new sub-
# processes etc.
if __name__ == '__main__':
    import contrast
    from contrast.environment import env, runCommand
    from contrast.environment.data import SdmPathFixer, PathFixer
    from contrast.environment.scheduling import MaxivScheduler
    from contrast.recorders import Hdf5Recorder, StreamRecorder #, ScicatRecorder
    from contrast.motors import DummyMotor, MotorMemorizer
    from contrast.motors.LC400 import LC400Motor
    from contrast.motors.TangoMotor import TangoMotor
    from contrast.motors.TangoAttributeMotor import TangoAttributeMotor
    from contrast.motors.SmaractMotor import SmaractLinearMotor
    from contrast.motors.SmaractMotor import SmaractRotationMotor
    from contrast.motors.NanosMotor import NanosMotor
    from contrast.motors.PiezoLegsMotor import PiezoLegsMotor
    from contrast.motors.PiezoLegsMotor import ImgSampleStage
    from contrast.motors.DacMotor import DacMotor
    from contrast.detectors.Eiger import Eiger
    from contrast.detectors.Xspress3 import Xspress3
    from contrast.detectors.AlbaEM import AlbaEM
    from contrast.detectors.PandaBox import PandaBox
    from contrast.detectors import Detector, PseudoDetector
    from contrast.detectors.BaslerCamera import BaslerCamera
    from contrast.scans import SoftwareScan, Ct
    import macros_common 
    import macros_img
    import os
    import time
    # add a scheduler to pause scans when shutters close
    """
    env.scheduler = MaxivScheduler(
                        shutter_list=['B303A-FE/VAC/HA-01',
                                      'B303A-FE/PSS/BS-01',
                                      'B303A-O/PSS/BS-01'],
                        avoid_injections=False,
                        respect_countdown=False,)
    """
    env.userLevel = 1
    # arbitrarily chosen these levels:
    # 1 - simple user
    # 2 - power user
    # 3 - optics
    # 4 - potentially dangerous

    # warn if we are not nanomax-service with correct umask
    user = os.popen('whoami').read().strip()
    umask = os.popen('umask').read().strip()
    if not (user == 'nanomax-service' and umask =='0022'):
        print(
            '\033[91mWARNING! The correct way of running the beamline'
            ' is as nanomax-service with umask 022\033[0m'
        )


    # sample piezos through National Instruments DAC device
    #xx = DacMotor(device='B303A/CTL/IMG-02', axis=0, name='xx', scaling=1.0, dial_limits=(-50,50), user_format='%.3f')
    #yy = DacMotor(device='B303A/CTL/IMG-02', axis=1, name='yy', dial_limits=(-50,50), user_format='%.3f')

    
    # Nanos motors for central stop, zone plate and order sorting aperture positioning
    """
    osax = NanosMotor(device='test/ctl/nanos-01', axis=0, name='osax', userlevel=1, scaling=-5e-4)
    osay = NanosMotor(device='test/ctl/nanos-01', axis=1, name='osay', userlevel=1, scaling=-5e-4)
    osaz = NanosMotor(device='test/ctl/nanos-01', axis=2, name='osaz', userlevel=-1, scaling=-5e-4)
    zpx = NanosMotor(device='test/ctl/nanos-01', axis=3, name='zpx', userlevel=1, scaling=5e-4)
    zpy = NanosMotor(device='test/ctl/nanos-01', axis=4, name='zpy', userlevel=1, scaling=-5e-4)
    zpz = NanosMotor(device='test/ctl/nanos-01', axis=5, name='zpz', userlevel=1, scaling=-5e-4)
    csx = NanosMotor(device='test/ctl/nanos-01', axis=6, name='csx', userlevel=1, scaling=-5e-4)
    csy = NanosMotor(device='test/ctl/nanos-01', axis=7, name='csy', userlevel=1, scaling=-5e-4)
    gry = NanosMotor(device='test/ctl/nanos-01', axis=8, name='gry', userlevel=1, scaling=-5e-4)
    grz = NanosMotor(device='test/ctl/nanos-01', axis=9, name='grz', userlevel=1, scaling=5e-4)
    gripper = NanosMotor(device='test/ctl/nanos-01', axis=10, name='gripper', userlevel=1, scaling=5e-4)
    nanos_dummy = NanosMotor(device='test/ctl/nanos-01', axis=11, name='nanos_dummy', userlevel=1, scaling=5e-4)
    """
    # PiezoLEGS motors for coarse sample positioning
    #bx, by, bz = ImgSampleStage(device='B303A/CTL/IMG-01', velocity=90, names=['bx', 'by', 'bz'], userlevel=1, scaling=1e-3, user_format='%.3f')
    #m0 = PiezoLegsMotor(device='B303A/CTL/IMG-01', axis=0, name='m0', userlevel=1, scaling=1e-3, user_format='%.3f')
    #m1 = PiezoLegsMotor(device='B303A/CTL/IMG-01', axis=1, name='m1', userlevel=1, scaling=1e-3, user_format='%.3f')
    #m2 = PiezoLegsMotor(device='B303A/CTL/IMG-01', axis=2, name='m2', userlevel=1, scaling=1e-3, user_format='%.3f')  

    # Smaract motors for sample rotation and first clean-up aperture positioning 
    sr = SmaractRotationMotor(device='B303A-EH/CTL/PZCU-06', axis=0, name='sr', velocity=10000, userlevel=1, user_format='%.4f', dial_format='%.4f')
    grx = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-06', axis=1, name='grx', velocity=10000, userlevel=1, user_format='%.3f', dial_format='%.3f')

    """
    pinhole_x = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-06', axis=3, name='pinhole_x', velocity=10000, userlevel=1, user_format='%.3f', dial_format='%.3f')
    pinhole_y = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-06', axis=4, name='pinhole_y', velocity=10000, userlevel=1, user_format='%.3f', dial_format='%.3f')
    mic = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-06', axis=5, name='mic', velocity=10000, userlevel=1, user_format='%.0f', dial_format='%.0f')
    np_x = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-06', axis=6, name='np_x', velocity=10000, userlevel=1, user_format='%.3f', dial_format='%.3f')
    np_y = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-06', axis=7, name='np_y', velocity=10000, scaling=-1, userlevel=1, user_format='%.3f', dial_format='%.3f')
    np_z = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-06', axis=8, name='np_z', velocity=10000, userlevel=1, user_format='%.3f', dial_format='%.3f')
    """
    # detectors
    #eiger4m = Eiger(name='eiger4m', host='b-nanomax-eiger-dc-1')
    #eiger1m = Eiger(name='eiger1m', host='b-nanomax-eiger-1m-0')
    #x3mini = Xspress3(name='x3mini', device='staff/alebjo/xspress3mini')
    #alba2 = AlbaEM(name='alba2', host='b-nanomax-em2-3')

    # The pandabox and some related pseudodetectors
    # Pandabox reading the LC400 encoders, both digital (AquadB) and analog
    #panda2 = PandaBox(name='panda2', host='b-nanomax-pandabox-2')
    #macros_common.Csnake.panda = panda2
    #macros_common.Csnake.dac_0 = xx
    #macros_common.Csnake.dac_1 = yy
    #macros_common.Cspiral.panda = panda2
    #macros_common.Cspiral.dac_0 = xx
    #macros_common.Cspiral.dac_1 = yy
    # Pandabox reading the Attocube (AquadB) encoders
    # panda3 = PandaBox(name='panda3', host='b-nanomax-pandabox-3')

    """
    pseudo = PseudoDetector(name='pseudo',
                            variables={'c1': 'panda2/INENC1.VAL_Mean',
                                       'c2': 'panda2/INENC2.VAL_Mean',
                                       'c3': 'panda2/INENC3.VAL_Mean',
                                       'a1': 'panda2/FMC_IN.VAL1_Mean',
                                       'a2': 'panda2/FMC_IN.VAL2_Mean',
                                       'a3': 'panda2/FMC_IN.VAL3_Mean'},
                            expression={'x': 'c1', 'y': 'c3', 'z': 'c2',
                                        'x_analog': 'a1',
                                        'y_analog': 'a3',
                                        'z_analog': 'a2'})
    """
    # the environment keeps track of where to write data
    #env.paths = SdmPathFixer('B303A-E01/CTL/SDM-01')
    env.paths = PathFixer()
    env.paths.directory = '/mxn/groups/nanomax/nimis/dac_scan'

    # an hdf5 recorder
    h5rec = Hdf5Recorder(name='h5rec')
    h5rec.start()

    # a zmq recorder
    zmqrec = StreamRecorder(name='zmqrec')
    zmqrec.start()  # removed for now

    # a scicat recorder - paused until further notice
    # scicatrec = ScicatRecorder(name='scicatrec')
    # scicatrec.start()

    # default detector selection
    for d in Detector.getinstances():
        d.active = False
    #for d in [panda2, pseudo, alba2]:
    #    d.active = True

    # define pre- and post-scan actions, per scan base class
    def pre_scan_stuff(slf):
        pass

    def post_scan_stuff(slf):
        pass

    SoftwareScan._before_scan = pre_scan_stuff
    SoftwareScan._after_scan = post_scan_stuff
    Ct._before_ct = pre_scan_stuff
    Ct._after_ct = post_scan_stuff

    contrast.wisdom()

    # find the latest scan number and initialize env.nextScanID
    try:
        l = os.listdir(env.paths.directory)
        last = max(
            [int(l_[:-3]) for l_ in l if (len(l_) == 9 and l_.endswith('.h5'))]
        )
        env.nextScanID = last + 1
        print(f'\nNote: inferring that the next scan number should be {last+1}')
    except:
        pass


    # add a memorizer so the motors keep their user positions and limits
    # after a restart note that this will overwrite the dial positions
    # set above! delete the file to generate it again.
    memorizer = MotorMemorizer(
        name='memorizer', filepath='/data/visitors/nanomax/common/sw/contrast_img/beamlines/nanomax/.memorizer')

    
