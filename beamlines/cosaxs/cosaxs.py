"""
The CoSAXS beamline at MAX IV.
"""

# need this main guard here because Process.start() (so our recorders)
# import __main__, and we don't want the subprocess to start new sub-
# processes etc.
if __name__ == '__main__':
    import contrast
    from contrast.environment import env, runCommand
    from contrast.environment.data import SdmPathFixer
    from contrast.environment.scheduling import MaxivScheduler
    from contrast.recorders import Hdf5Recorder, StreamRecorder #, ScicatRecorder
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
    from contrast.motors.E727 import E727Motor
    from contrast.detectors.Eiger import Eiger
    from contrast.detectors.Xspress3 import Xspress3
    from contrast.detectors.AlbaEM import AlbaEM
    from contrast.detectors.PandaBox import PandaBox
    from contrast.detectors import Detector, PseudoDetector
    from contrast.scans import SoftwareScan, Ct
    import macros # beamline specific macros
    import os
    import time


    # the environment keeps track of where to write data
    env.paths = SdmPathFixer('b310a/ctl/sdm-01')

    """## commented out fr now desc = Failed to connect to database on host g-v-csproxy-0.maxiv.lu.se with port 10303
    # add a scheduler to pause scans when shutters close
    env.scheduler = MaxivScheduler(
                        shutter_list=['b310a-fe/vac/ha-01',
                                      'b310a-fe/pss/bs-01',
                                      'b310a-o/pss/bs-01'],
                        avoid_injections=False,
                        respect_countdown=False,)
    """


    env.userLevel = 2
    # arbitrarily chosen these levels:
    # 1 - simple user
    # 2 - power user
    # 3 - optics
    # 4 - potentially dangerous

    ########################################
    # motors
    ########################################

    # some dummy motors
    dummy1 = DummyMotor(name='dummy1', userlevel=2)
    dummy1.velocity = 100
    dummy2 = DummyMotor(name='dummy2', userlevel=2)
    dummy2.velocity = 100

    # PI NanoCube 3-axis piezo. To be used in temporary setups
    sx = E727Motor(device='B310A/CTL/PZCU-01', axis=2, name='sx', userlevel=1, scaling=-1.0, dial_limits=(0,100), user_format='%.3f', dial_format='%.3f')
    sy = E727Motor(device='B310A/CTL/PZCU-01', axis=3, name='sy', userlevel=1, scaling=+1.0, dial_limits=(0,100), user_format='%.3f', dial_format='%.3f')
    sz = E727Motor(device='B310A/CTL/PZCU-01', axis=1, name='sz', userlevel=1, scaling=+1.0, dial_limits=(0,100), user_format='%.3f', dial_format='%.3f')

    # undulator
    ivu_gap = TangoMotor(device='b-v-cosaxs-csdb-0:10000/motor/gap_ctrl/1', name='ivu_gap', userlevel=2, dial_limits=(4.599, 49.9), user_format='%.4f')
    energy = TangoMotor(device='b-v-cosaxs-csdb-0:10000/pm/mono_bragg_ctrl/1', name='energy', userlevel=2, dial_limits=(5000, 32000), user_format='%.1f', scaling=1000.)

    # detector table inside the flight tube
    det_x = TangoMotor(device='b-v-cosaxs-csdb-0:10000/b310a-e02/dia/tab-02-x', name='det_x', userlevel=2, dial_limits=(42, 200), user_format='%.4f')
    det_y = TangoMotor(device='b-v-cosaxs-csdb-0:10000/b310a-e02/dia/tab-02-y', name='det_y', userlevel=2, dial_limits=(36, 199), user_format='%.4f')
    det_z = TangoMotor(device='b-v-cosaxs-csdb-0:10000/motor/cosaxs_flight_ctrl/26', name='det_z', userlevel=2, dial_limits=(-569.65, 13865.0), user_format='%.4f')

    # pinhole - Thorlabs stages
    pinhole_x = TangoMotor(device='b-v-cosaxs-csdb-0:10000/b310a-e01/dia/sams-01-x', name='pinhole_x', userlevel=2, scaling= 1.0,dial_limits=(-5000, 5000), user_format='%.4f')
    pinhole_y = TangoMotor(device='b-v-cosaxs-csdb-0:10000/b310a-e01/dia/sams-01-y', name='pinhole_y', userlevel=2, scaling=-1.0, dial_limits=(-5000, 5000), user_format='%.4f')

    # sample - Huber stages
    sample_x = TangoMotor(device='b-v-cosaxs-csdb-0:10000/b310a-e01/dia/sams-04-x', name='sample_x', userlevel=2, dial_limits=(10, 290), user_format='%.4f')
    sample_y = TangoMotor(device='b-v-cosaxs-csdb-0:10000/b310a-e01/dia/sams-04-y', name='sample_y', userlevel=2, dial_limits=(10, 80), user_format='%.4f')


    # attenuators
    bcu01_x1pz = TangoMotor(device='b-v-cosaxs-csdb-0:10000/b310a-e01/dia/bcu01-x1pz', name='bcu01_x1pz', userlevel=2, dial_limits=(-20, 20), user_format='%.4f')
    bcu01_x2pz = TangoMotor(device='b-v-cosaxs-csdb-0:10000/b310a-e01/dia/bcu01-x2pz', name='bcu01_x2pz', userlevel=2, dial_limits=(-20, 20), user_format='%.4f')
    # bcu01_x1pz                       bcu01_x2pz
    #  32 - out - no absorber           32 - out - no absorber
    #  21 - Al 18um                     21 - Ti 75um
    #  10 - Al 60um                     10 - Ti 225um
    #   0 - Al 180um                     0 - Ti 375um
    # -10 - Al 540um                   -10 - Ti 525um
    # -20 - Al 1020um                  -20 - Ti 675um

    # slit 1 - for setting the coherence
    slit1_xl = TangoMotor(device='b-v-cosaxs-csdb-0:10000/b310a-o02/opt/slit-01-xl', name='slit1_xl', userlevel=2, dial_limits=(-20, 20), user_format='%.4f') #mm
    slit1_xr = TangoMotor(device='b-v-cosaxs-csdb-0:10000/b310a-o02/opt/slit-01-xr', name='slit1_xr', userlevel=2, dial_limits=(-20, 20), user_format='%.4f')
    slit1_yb = TangoMotor(device='b-v-cosaxs-csdb-0:10000/b310a-o02/opt/slit-01-yb', name='slit1_yb', userlevel=2, dial_limits=(-20, 20), user_format='%.4f')
    slit1_yt = TangoMotor(device='b-v-cosaxs-csdb-0:10000/b310a-o02/opt/slit-01-yt', name='slit1_yt', userlevel=2, dial_limits=(-20, 20), user_format='%.4f')
    slit1_xgap = TangoMotor(device='b-v-cosaxs-csdb-0:10000/pm/o02_v_slit1_ctrl/1', name='slit1_xgap', userlevel=2, dial_limits=(-20, 20), user_format='%.4f') #mm
    slit1_xpos = TangoMotor(device='b-v-cosaxs-csdb-0:10000/pm/o02_v_slit1_ctrl/2', name='slit1_xpos', userlevel=2, dial_limits=(-20, 20), user_format='%.4f')
    slit1_ygap = TangoMotor(device='b-v-cosaxs-csdb-0:10000/pm/o02_h_slit1_ctrl/1', name='slit1_ygap', userlevel=2, dial_limits=(-20, 20), user_format='%.4f')
    slit1_ypos = TangoMotor(device='b-v-cosaxs-csdb-0:10000/pm/o02_h_slit1_ctrl/2', name='slit1_ypos', userlevel=2, dial_limits=(-20, 20), user_format='%.4f')

    # granite table
    table_x = TangoMotor(device='b-v-cosaxs-csdb-0:10000/b310a-e01/dia/tab-01-x', name='table_x', userlevel=2, dial_limits=(-11.6, 11.15), user_format='%.4f') #mm
    table_y = TangoMotor(device='b-v-cosaxs-csdb-0:10000/b310a-e01/dia/tab-01-y', name='table_y', userlevel=2, dial_limits=(-11.6, 11.15), user_format='%.4f')

    ########################################
    # detectors
    ########################################

    eiger4m = Eiger(name='eiger4m', host='b-cosaxs-eiger-dc-0',  use_image_appendix=True) # 172.16.197.26
    panda0 = PandaBox(name='panda0', host='b-cosaxs-pandabox-0') # 172.16.198.70
    alba0 = AlbaEM(name='alba0', host='172.16.198.48') #172.16.198.48 # maybe channel 2
    pseudo = PseudoDetector(name='pseudo',
                            variables={'I0_m': 'panda0/FMC_IN.VAL6_Mean',
                                       'It_m': 'panda0/FMC_IN.VAL3_Mean'},
                            expression={'I0': 'I0_m', 
                                        'It': 'It_m'})

    ########################################
    # recorders
    ########################################

    # an hdf5 recorder
    h5rec = Hdf5Recorder(name='h5rec')
    h5rec.start()

    # a zmq recorder
    zmqrec = StreamRecorder(name='zmqrec')
    zmqrec.start()  # removed for now

    # a scicat recorder - paused until further notice
    # scicatrec = ScicatRecorder(name='scicatrec')
    # scicatrec.start()

    # default detector selection on contrast startup
    for d in Detector.getinstances():
        d.active = False
    for d in [panda0, alba0, pseudo, eiger4m]:
        d.active = True

    # define pre- and post-scan actions, per scan base class
    def pre_scan_stuff(slf):
        runCommand('stoplive')
        runCommand('fsopen')
        pass

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
        print('\nNote: inferring that the next scan number should be %u'
              % (last + 1))
    except:
        pass

    # add a memorizer so the motors keep their user positions and limits
    # after a restart note that this will overwrite the dial positions
    # set above! delete the file to generate it again.
    memorizer = MotorMemorizer(
        name='memorizer', filepath='/mxn/home/cosaxs-user/data-visitors/common/sw/contrast/beamlines/cosaxs/.memorizer')
