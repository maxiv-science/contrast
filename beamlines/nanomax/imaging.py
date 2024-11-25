"""
The imaging endstation at NanoMAX.
"""

# need this main guard here because Process.start() (so our recorders)
# import __main__, and we don't want the subprocess to start new sub-
# processes etc.
if __name__ == '__main__':
    import contrast
    from contrast.environment import env, runCommand
    from contrast.environment.data import SdmPathFixer
    from contrast.environment.scheduling import MaxivScheduler
    from contrast.recorders import Hdf5Recorder, StreamRecorder, ScicatRecorder
    from contrast.motors import DummyMotor, MotorMemorizer
    from contrast.motors.E727 import E727Motor
    from contrast.motors.LC400 import LC400Motor
    from contrast.motors.TangoMotor import TangoMotor
    from contrast.motors.TangoAttributeMotor import TangoAttributeMotor
    from contrast.motors.SmaractMotor import SmaractLinearMotor
    from contrast.motors.SmaractMotor import SmaractRotationMotor
    from contrast.motors.NanosMotor import NanosMotor
    from contrast.motors.PiezoLegsMotor import PiezoLegsMotor
    from contrast.motors.PiezoLegsMotor import ImgSampleStage
    from contrast.motors.DacMotor import DacMotor
    from contrast.detectors.Eiger import Eiger, EigerTango
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

    # dissable ipython auto-completion/suggestions
    # taken from https://github.com/ipython/ipython/issues/13451#issuecomment-1014526360
    import IPython
    terminal = IPython.get_ipython()
    terminal.pt_app.auto_suggest = None

    # warn if we are not nanomax-service with correct umask
    user = os.popen('whoami').read().strip()
    umask = os.popen('umask').read().strip()
    if not (user == 'nanomax-service' and umask =='0022'):
        print(
            '\033[91mWARNING! The correct way of running the beamline'
            ' is as nanomax-service with umask 022\033[0m'
        )

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

    #######################################################################################################
    # Beamline equipment. Comment out when not used
    #######################################################################################################
    """
    # gap and taper via a proxy in the local pool
    ivu_gap = TangoMotor(device='motor/ivu_gap_ctrl/1', name='ivu_gap', userlevel=2, dial_limits=(4.5, 25), user_format='%.4f')
    ivu_taper = TangoMotor(device='motor/ivu_taper_ctrl/1', name='ivu_taper', userlevel=4, dial_limits=(-.05, .05), user_format='%.4f')

    # Diamond filter motors, sitting in diagnostics module 1
    #bl_filter_1 = TangoMotor(device='b303a-o/opt/flt-01-yml', name='bl_filter_1', userlevel=6, dial_limits=(-36.04, 36.77))
    #bl_filter_2 = TangoMotor(device='b303a-o/opt/flt-02-yml', name='bl_filter_2', userlevel=6, dial_limits=(-36.24, 38.46))

    # Vertical focusing mirror motors
    vfm_x = TangoMotor(device='b303a-o/opt/mir-01-xml', name='vfm_x', userlevel=6, dial_limits=(-4.53, 1.2), user_format='%.3f')
    vfm_y = TangoMotor(device='b303a-o/opt/mir-01-yml', name='vfm_y', userlevel=6, dial_limits=(-15.24, 15.91), user_format='%.3f')
    vfm_pit = TangoMotor(device='b303a-o/opt/mir-01-pitml', name='vfm_pit', userlevel=6, dial_limits=(2.65, 2.85), user_format='%.3f')
    vfm_yaw = TangoMotor(device='b303a-o/opt/mir-01-yawml', name='vfm_yaw', userlevel=6, dial_limits=(-1.43, 1.42), user_format='%.3f')

    # Horizontal focusing mirror motors
    hfm_x = TangoMotor(device='b303a-o/opt/mir-02-xml', name='hfm_x', userlevel=6, dial_limits=(-2.05, 0.1), user_format='%.3f')
    hfm_y = TangoMotor(device='b303a-o/opt/mir-02-yml', name='hfm_y', userlevel=2, dial_limits=(-15.33, 14.71), user_format='%.3f')
    hfm_pit = TangoMotor(device='b303a-o/opt/mir-02-pitml', name='hfm_pit', userlevel=6, dial_limits=(2.65, 2.85), user_format='%.3f')
    hfm_bend = TangoMotor(device='b303a-o/opt/mir-02-bendml', name='hfm_bend', userlevel=6)

    # Monochromator motors
    mono_x = TangoMotor(device='b303a-o/opt/mono-xml', name='mono_x', userlevel=6, dial_limits=(-2.4, 3.87), user_format='%.3f')
    mono_bragg = TangoMotor(device='b303a-o/opt/MONO-BRAGML', name='mono_bragg', userlevel=4, dial_limits=(4.0, 27.46))
    mono_x2per = TangoMotor(device='b303a-o/opt/mono-perml', name='mono_x2per', userlevel=2, dial_limits=(-.1, .1), user_format='%.3f')
    mono_x2pit = TangoMotor(device='b303a-o/opt/mono-pitml', name='mono_x2pit', userlevel=4, dial_limits=(-1.21, 1.21), user_format='%.4f')
    mono_x2rol = TangoMotor(device='b303a-o/opt/mono-rolml', name='mono_x2rol', userlevel=4, dial_limits=(-0.8, 0.79), user_format='%.4f')
    mono_x2fpit = TangoMotor(device='B303A-O/CTL/PZCU-01', name='mono_x2fpit', userlevel=4, dial_limits=(0., 12.), user_format='%.2f')
    mono_x2frol = TangoMotor(device='B303A-O/CTL/PZCU-02', name='mono_x2frol', userlevel=4, dial_limits=(0., 12.), user_format='%.2f')

    # Nanobpm motor. Positions the bpm vertically in the beam. Almost never moved. Should be at 2.5 mm
    #nanobpm_y = TangoMotor(device='b303a-o/dia/bpx-01', name='nanobpm_y', userlevel=6, dial_limits=(-0.1, 23.1))
    
    # smaracts
    # controller 2
    dbpm2_x = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-04', axis=0, name='dbpm2_x', userlevel=6)
    dbpm2_y = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-04', axis=1, name='dbpm2_y', userlevel=6)
    seh_top = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-04', axis=2, name='seh_top', userlevel=3)
    seh_bottom = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-04', axis=3, name='seh_bottom', userlevel=3)
    seh_left = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-04', axis=4, name='seh_left', userlevel=3)
    seh_right = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-04', axis=5, name='seh_right', userlevel=3)
    attenuator1_x = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-04', axis=6, name='attenuator1_x', userlevel=2)
    attenuator2_x = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-04', axis=7, name='attenuator2_x', userlevel=2)
    #attenuator3_x = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-04', axis=8, name='attenuator3_x', userlevel=2)   #declared in common macro attenuate
    attenuator4_x = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-04', axis=9, name='attenuator4_x', userlevel=2)
    # fastshutter_x = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-04', axis=10, name='fastshutter_x', userlevel=3)
    diode1_x = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-04', axis=11, name='diode1_x', userlevel=3, frequency=1000)
    pol_x = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-04', axis=12, name='pol_x', userlevel=3, frequency=1000)
    pol_y = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-04', axis=13, name='pol_y', userlevel=3, frequency=1000)
    pol_rot = SmaractRotationMotor(device='B303A-EH/CTL/PZCU-04', axis=14, name='pol_rot', userlevel=3, user_format='%.8f', dial_format='%.8f')

    # controller 4 in OH2 for fast shutter and first diamondBPM
    # fastshutter_y = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-07', axis=0, name='fastshutter_y', userlevel=3)#)
    dbpm1_x = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-07', axis=1, name='dbpm1_x', userlevel=3)#)
    dbpm1_y = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-07', axis=2, name='dbpm1_y', userlevel=3)#)

    # SSA through the Pool
    ssa_gapx = TangoMotor(device='B303A-O/opt/SLIT-01-GAPXPM', name='ssa_gapx', userlevel=2)
    ssa_gapy = TangoMotor(device='B303A-O/opt/SLIT-01-GAPYPM', name='ssa_gapy', userlevel=2)
    ssa_posx = TangoMotor(device='B303A-O/opt/SLIT-01-POSXPM', name='ssa_posx', userlevel=3)
    ssa_posy = TangoMotor(device='B303A-O/opt/SLIT-01-POSYPM', name='ssa_posy', userlevel=3)

    # some sardana pseudo motors - these are reimplemented but just need to be configured
    energy_raw = TangoMotor(device='pseudomotor/nanomaxenergy_ctrl/1', name='energy_raw')
    energy = TangoMotor(device='pseudomotor/nanomaxenergy_corr_ctrl/1', name='energy')

    # a zmq recorder
    zmqrec = StreamRecorder(name='zmqrec')
    zmqrec.start()  # removed for now
    """
    #######################################################################################################
    # Experimental station equipment
    #######################################################################################################


    # KB mirror pitch piezos
    m1pitch = E727Motor(device='B303A-E01/CTL/PZCU-04', axis=1, name='m1pitch', userlevel=2, user_format='%.3f', dial_format='%.3f', dial_limits=(0,30))
    m2pitch = E727Motor(device='B303A-E01/CTL/PZCU-04', axis=2, name='m2pitch', userlevel=2, user_format='%.3f', dial_format='%.3f', dial_limits=(0,30))
    m1roll = E727Motor(device='B303A-E01/CTL/PZCU-04', axis=3, name='m1roll', userlevel=2, user_format='%.3f', dial_format='%.3f', dial_limits=(0,30))
     
    # sample piezos through National Instruments DAC device
    sx = DacMotor(device='B303A/CTL/IMG-02', axis=0, name='sx', scaling=1.0, dial_limits=(-50,50), user_format='%.3f')
    sy = DacMotor(device='B303A/CTL/IMG-02', axis=1, name='sy', scaling=1.0, dial_limits=(-50,50), user_format='%.3f')
    sz = DacMotor(device='B303A/CTL/IMG-02', axis=2, name='sz', scaling=1.0, dial_limits=(-50,50), user_format='%.3f')
    """
    # Nanos motors for central stop, zone plate and order sorting aperture positioning
    osax = NanosMotor(device='test/ctl/nanos-01', axis=0, name='osax', velocity=500, stop_window=10, userlevel=2, scaling=-5e-4)
    osay = NanosMotor(device='test/ctl/nanos-01', axis=1, name='osay', velocity=500, stop_window=10, userlevel=2, scaling=-5e-4)
    osaz = NanosMotor(device='test/ctl/nanos-01', axis=2, name='osaz', velocity=500, stop_window=10, userlevel=2, scaling=-5e-4)
    zpx = NanosMotor(device='test/ctl/nanos-01', axis=3, name='zpx', velocity=500, stop_window=10, userlevel=2, scaling=5e-4)
    zpy = NanosMotor(device='test/ctl/nanos-01', axis=4, name='zpy', velocity=500, stop_window=10, userlevel=2, scaling=-5e-4)
    zpz = NanosMotor(device='test/ctl/nanos-01', axis=5, name='zpz', velocity=500, stop_window=10, userlevel=2, scaling=-5e-4)
    csx = NanosMotor(device='test/ctl/nanos-01', axis=6, name='csx', velocity=500, stop_window=10, userlevel=2, scaling=-5e-4)
    csy = NanosMotor(device='test/ctl/nanos-01', axis=7, name='csy', velocity=500, stop_window=10, userlevel=2, scaling=-5e-4)
    """

    gry = NanosMotor(device='test/ctl/nanos-01', axis=11, name='gry', velocity=500, stop_window=10000, userlevel=1, scaling=-5e-4)
    grz = NanosMotor(device='test/ctl/nanos-01', axis=9, name='grz', velocity=500, stop_window=10000, userlevel=1, scaling=5e-4)
    gripper = NanosMotor(device='test/ctl/nanos-01', axis=10, name='gripper', velocity=500, stop_window=10000, userlevel=1, scaling=5e-4)
    #nanos_dummy = NanosMotor(device='test/ctl/nanos-01', axis=11, name='nanos_dummy', userlevel=1, scaling=5e-4)


    # PiezoLEGS motors for coarse sample positioning
    basex, basey, basez = ImgSampleStage(device='B303A-E01/CTL/PZCU-02', velocity=90, names=['basex', 'basey', 'basez'], userlevel=1, scaling=1e-3, user_format='%.3f')

    
    # Smaract motors for sample rotation and first clean-up aperture positioning 
    sr = SmaractRotationMotor(device='B303A-E01/CTL/PZCU-01', axis=0, name='sr', frequency=500, userlevel=1, user_format='%.4f', dial_format='%.4f')
    grx = SmaractLinearMotor(device='B303A-E01/CTL/PZCU-01', axis=1, name='grx', frequency=500, userlevel=1, user_format='%.3f', dial_format='%.3f')
    apx = SmaractLinearMotor(device='B303A-E01/CTL/PZCU-01', axis=15, name='apx', frequency=1000, userlevel=1, user_format='%.3f', dial_format='%.3f')
    apy = SmaractLinearMotor(device='B303A-E01/CTL/PZCU-01', axis=16, name='apy', frequency=1000, userlevel=1, user_format='%.3f', dial_format='%.3f')
    
    # Pixel detector and XRF motors, optical microsope and screen motors
    xrf1_x = TangoMotor(device='B303A-E01/DIA/XRF-01-X', name='xrf1_x', userlevel=2, user_format='%.3f')
    xrf2_x = TangoMotor(device='B303A-E01/DIA/XRF-02-X', name='xrf2_x', userlevel=2, user_format='%.3f')
    pixdet_x = TangoMotor(device='B303A-E01/DIA/PIXDET-X', name='pixdet_x', userlevel=2, user_format='%.3f')
    pixdet_y = TangoMotor(device='B303A-E01/DIA/PIXDET-Y', name='pixdet_y', userlevel=2, user_format='%.3f')
    screen = TangoMotor(device='B303A-E01/DIA/OPT-SCR', name='screen', userlevel=1, user_format='%.3f')
    mic = TangoMotor(device='B303A-E01/DIA/OPT-MIC', name='mic', userlevel=1, user_format='%.3f')

    # some dummy motors
    dummy1 = DummyMotor(name='dummy1', userlevel=3)
    dummy2 = DummyMotor(name='dummy2', userlevel=3)
    # detectors
    #eiger4m = Eiger(name='eiger4m', host='b-nanomax-eiger-dc-1')
    eiger4m = EigerTango('b303a/dia/eiger-4m', name='eiger4m', rotation=2)

    x3mini = Xspress3(name='x3mini', device='staff/alebjo/xspress3mini')
    #E01cam01 = BaslerCamera(name='E01cam01', device='basler/e01-cam-01/main')
    #E01cam02 = BaslerCamera(name='E01cam02', device='basler/e01-cam-02/main')
    #E01cam03 = BaslerCamera(name='E01cam03', device='basler/e01-cam-03/main')
    #E01cam04 = BaslerCamera(name='E01cam04', device='basler/e01-cam-04/main')

    #alba2 = AlbaEM(name='alba2', host='b-nanomax-em2-2')

    # The pandabox and some related pseudodetectors
    # Pandabox reading the LC400 encoders analog and controlling the fast shutter
    panda2 = PandaBox(name='panda2', host='b-nanomax-pandabox-2')

    macros_img.WFtrigscan.panda = panda2
    macros_img.WFtrigscan.dac_0 = sx
    macros_img.WFtrigscan.dac_1 = sy
    macros_img.WFtrigscan.dac_2 = sz

    pseudo = PseudoDetector(name='pseudo',
                            variables={'c1': 'panda2/INENC1.VAL_Mean',
                                       'c2': 'panda2/INENC2.VAL_Mean',
                                       'c3': 'panda2/INENC3.VAL_Mean',
                                       'a1': 'panda2/FMC_IN.VAL1_Mean',
                                       'a2': 'panda2/FMC_IN.VAL2_Mean',
                                       'a3': 'panda2/FMC_IN.VAL3_Mean',
                                       'a4': 'panda2/FMC_IN.VAL4_Mean'},
                            expression={'laser_x': 'c1', 
                                        'laser_y': 'c2', 
                                        'laser_z': 'c3',
                                        'x': 'a1',
                                        'y': 'a3',
                                        'z': 'a2',
                                        'ai4': 'a4'})

    # the environment keeps track of where to write data
    env.paths = SdmPathFixer('B303A-E01/CTL/SDM-01')

    # an hdf5 recorder
    h5rec = Hdf5Recorder(name='h5rec')
    h5rec.start()

    # a scicat recorder - paused until further notice
    #scicatrec = ScicatRecorder(name='scicatrec', pathfixer='b303a-e01/ctl/sdm-01')
    #scicatrec.start()

    # default detector selection
    for d in Detector.getinstances():
        d.active = False
    for d in [panda2, pseudo, eiger4m]:
        d.active = True

    # define pre- and post-scan actions, per scan base class
    def pre_scan_stuff(slf):
        assert h5rec.is_alive(), 'hdf5 recorder is dead! this can''t be good. maybe restart contrast.'
        runCommand('stoplive')
        runCommand('optics on')
        runCommand('fsopen')
        #basex.stop()   # making sure the base motor are not regulating
        #basey.stop()   # making sure the base motors are not regulating
        time.sleep(0.2)

    def post_scan_stuff(slf):
        runCommand('fsclose')
        pass

    SoftwareScan._before_scan = pre_scan_stuff
    SoftwareScan._after_scan = post_scan_stuff
    Ct._before_ct = pre_scan_stuff
    Ct._after_ct = post_scan_stuff

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

    # chech git repo status at the start
    runCommand('checkgit')

    # contrast startup message with random acronym
    contrast.wisdom()
