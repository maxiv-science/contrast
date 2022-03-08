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
    from contrast.motors.LC400 import LC400Motor
    from contrast.motors.TangoMotor import TangoMotor
    from contrast.motors.TangoAttributeMotor import TangoAttributeMotor
    from contrast.motors.SmaractMotor import SmaractLinearMotor
    from contrast.motors.SmaractMotor import SmaractRotationMotor
    from contrast.motors.NanosMotor import NanosMotor
    from contrast.motors.Pmd401Motor import Pmd401Motor
    from contrast.motors.Pmd401Motor import BaseYMotor
    from contrast.motors.Pmd401Motor import BaseZMotor
    from contrast.detectors.Eiger import Eiger
    from contrast.detectors.Xspress3 import Xspress3
    from contrast.detectors.AlbaEM import AlbaEM
    from contrast.detectors.PandaBox import PandaBox
    from contrast.detectors import Detector, PseudoDetector
    from contrast.scans import SoftwareScan, Ct
    from macros_common import *
    from macros_img import *
    import os
    import time

    # add a scheduler to pause scans when shutters close
    env.scheduler = MaxivScheduler(
                        shutter_list=['B303A-FE/VAC/HA-01',
                                      'B303A-FE/PSS/BS-01',
                                      'B303A-O/PSS/BS-01'],
                        avoid_injections=False,
                        respect_countdown=False,)

    env.userLevel = 2
    # arbitrarily chosen these levels:
    # 1 - simple user
    # 2 - power user
    # 3 - optics
    # 4 - potentially dangerous

    # Nanos motors for central stop, zone plate and order sorting aperture positioning
    zpx = NanosMotor(device='staff/ulfjoh/nanos-1', axis=4, name='zpx', userlevel=1, scaling=5e-4)
    zpy = NanosMotor(device='staff/ulfjoh/nanos-1', axis=5, name='zpy', userlevel=1, scaling=-5e-4)
    zpz = NanosMotor(device='staff/ulfjoh/nanos-1', axis=8, name='zpz', userlevel=1, scaling=-5e-4)
    csx = NanosMotor(device='staff/ulfjoh/nanos-1', axis=9, name='csx', userlevel=1, scaling=-5e-4)
    csy = NanosMotor(device='staff/ulfjoh/nanos-1', axis=12, name='csy', userlevel=1, scaling=-5e-4)
    osax = NanosMotor(device='staff/ulfjoh/nanos-1', axis=13, name='osax', userlevel=1, scaling=-5e-4)
    osay = NanosMotor(device='staff/ulfjoh/nanos-1', axis=14, name='osay', userlevel=1, scaling=-5e-4)
    osaz = NanosMotor(device='staff/ulfjoh/nanos-1', axis=15, name='osaz', userlevel=1, scaling=-5e-4)
    # m16 = NanosMotor(device='staff/ulfjoh/nanos-1', axis=16, name='m16', userlevel=1, scaling=-5e-4)
    # m17 = NanosMotor(device='staff/ulfjoh/nanos-1', axis=17, name='m17', userlevel=1, scaling=-5e-4)

    # PiezoLEGS motors for coarse sample positioning
    bx = Pmd401Motor(device='test/ctl/pmd-01', axis=0, name='bx', userlevel=1, scaling=1e-3, user_format='%.3f')
    b1 = Pmd401Motor(device='test/ctl/pmd-01', axis=1, name='b1', userlevel=1, scaling=1e-3, user_format='%.3f')
    b2 = Pmd401Motor(device='test/ctl/pmd-01', axis=2, name='b2', userlevel=1, scaling=1e-3, user_format='%.3f')  
    by = BaseYMotor(motors=(b1, b2), name='by', dry_run=False, userlevel=1, user_format='%.3f')   
    bz = BaseZMotor(motors=(b1, b2), name='bz', dry_run=False, userlevel=1, user_format='%.3f')   

    # Smaract motors for sample rotation and first clean-up aperture positioning 
    pinhole_x = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-06', axis=0, name='pinhole_x', userlevel=1, user_format='%.3f', dial_format='%.3f')
    pinhole_y = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-06', axis=1, name='pinhole_y', userlevel=1, user_format='%.3f', dial_format='%.3f')
    sr = SmaractRotationMotor(device='B303A-EH/CTL/PZCU-06', axis=2, name='sr', userlevel=1, user_format='%.4f', dial_format='%.4f', velocity=3000000)

    # sample piezos
    sx = LC400Motor(device='B303A/CTL/PZCU-LC400B', axis=1, name='sx', scaling=1.0, dial_limits=(-50,50), user_format='%.3f')
    sy = LC400Motor(device='B303A/CTL/PZCU-LC400B', axis=3, name='sy', dial_limits=(-50,50), user_format='%.3f')
    sz = LC400Motor(device='B303A/CTL/PZCU-LC400B', axis=2, name='sz', scaling=-1.0, dial_limits=(-50,50), user_format='%.3f')

    # gap and taper
    ivu_gap = TangoMotor(device='g-v-csproxy-0:10000/r3-303l/id/idivu-01_gap', name='ivu_gap', userlevel=2, dial_limits=(4.5, 25), user_format='%.4f')
    ivu_taper = TangoMotor(device='g-v-csproxy-0:10000/r3-303l/id/idivu-01_taper', name='ivu_taper', userlevel=4, dial_limits=(-.05, .05), user_format='%.4f')

    # Diamond filter motors, sitting in diagnostics module 1
    bl_filter_1 = TangoMotor(device='b303a-o/opt/flt-01-yml', name='bl_filter_1', userlevel=6, dial_limits=(-36.04, 36.77))
    bl_filter_2 = TangoMotor(device='b303a-o/opt/flt-02-yml', name='bl_filter_2', userlevel=6, dial_limits=(-36.24, 38.46))

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
    mono_x2fpit = TangoMotor(device='B303A-O/CTL/PZCU-01', name='mono_x2fpit', userlevel=1, dial_limits=(0., 12.), user_format='%.2f')
    mono_x2frol = TangoMotor(device='B303A-O/CTL/PZCU-02', name='mono_x2frol', userlevel=1, dial_limits=(0., 12.), user_format='%.2f')

    # Nanobpm motor. Positions the bpm vertically in the beam. Almost never moved. Should be at 2.5 mm
    nanobpm_y = TangoMotor(device='b303a-o/dia/bpx-01', name='nanobpm_y', userlevel=6, dial_limits=(-0.1, 23.1))

    # smaracts
    # controller 2
    dbpm2_x = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-04', axis=0, name='dbpm2_x', userlevel=3)
    dbpm2_y = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-04', axis=1, name='dbpm2_y', userlevel=3)
    seh_top = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-04', axis=2, name='seh_top', userlevel=1)
    seh_bottom = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-04', axis=3, name='seh_bottom', userlevel=3)
    seh_left = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-04', axis=4, name='seh_left', userlevel=3)
    seh_right = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-04', axis=5, name='seh_right', userlevel=3)
    attenuator1_x = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-04', axis=6, name='attenuator1_x', userlevel=2)
    attenuator2_x = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-04', axis=7, name='attenuator2_x', userlevel=2)
    attenuator3_x = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-04', axis=8, name='attenuator3_x', userlevel=2)
    attenuator4_x = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-04', axis=9, name='attenuator4_x', userlevel=2)
    diode1_x = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-04', axis=11, name='diode1_x', userlevel=3)

    # controller 3
    # diode2_y = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-05', axis=0, name='diode2_y', userlevel=3)#)
    # diode2_z = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-05', axis=1, name='diode2_z', userlevel=3)#)
    # diode2_x = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-05', axis=2, name='diode2_x', userlevel=3)#)

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

    # some dummy motors
    dummy1 = DummyMotor(name='dummy1', userlevel=2)
    dummy2 = DummyMotor(name='dummy2', userlevel=2)

    # detectors
    eiger = Eiger(name='eiger', host='b-nanomax-eiger-dc-1')
    xspress3 = Xspress3(name='xspress3', device='staff/alebjo/xspress3')
    alba0 = AlbaEM(name='alba0', host='b-nanomax-em2-0')

    # The pandabox and some related pseudodetectors
    # Pandabox at the diffraction station, which is needed for controlling the fast shutter
    panda0 = PandaBox(name='panda0', host='b-nanomax-pandabox-0')
    # Pandabox reading the LC400 encoders, both digital (AquadB) and analog
    panda2 = PandaBox(name='panda2', host='b-nanomax-pandabox-2')
    NpointFlyscan.panda = panda2
    # Pandabox reading the Attocube (AquadB) encoders
    # panda3 = PandaBox(name='panda3', host='b-nanomax-pandabox-3')

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

    # the environment keeps track of where to write data
    env.paths = SdmPathFixer('B303A-E01/CTL/SDM-01')

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
    for d in [panda2, pseudo, eiger]:
        d.active = True

    # define pre- and post-scan actions, per scan base class
    def pre_scan_stuff(slf):
        runCommand('stoplive')
        runCommand('fsopen')
        b1.stop()   # making sure the base motors are not regulating
        time.sleep(0.2)

    def post_scan_stuff(slf):
        runCommand('fsclose')
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
        name='memorizer', filepath='/mxn/groups/nanomax/nimis/sw/.memorizer')
