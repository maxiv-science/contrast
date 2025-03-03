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
    from contrast.detectors.Eiger import Eiger, EigerTango, SelunTango
    from contrast.detectors.Xspress3 import Xspress3
    from contrast.detectors.AlbaEM import AlbaEM
    from contrast.detectors.PandaBox import PandaBox
    from contrast.detectors import Detector, PseudoDetector
    from contrast.detectors.BaslerCamera import BaslerCamera
    from contrast.scans import SoftwareScan, Ct
    #import macros_common
    #import macros_img
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
    
    # some sardana pseudo motors - these are reimplemented but just need to be configured
    energy_raw = TangoMotor(device='pseudomotor/nanomaxenergy_ctrl/1', name='energy_raw')
    energy = TangoMotor(device='pseudomotor/nanomaxenergy_corr_ctrl/1', name='energy')

    # a zmq recorder
    zmqrec = StreamRecorder(name='zmqrec', port=5556)
    zmqrec.start()  # removed for now
    
    #######################################################################################################
    # Experimental station equipment
    #######################################################################################################


    # some dummy motors
    dummy1 = DummyMotor(name='dummy1', userlevel=3)
    dummy2 = DummyMotor(name='dummy2', userlevel=3)
    # detectors
    #eiger4m = Eiger(name='eiger4m', host='b-nanomax-eiger-dc-1')
    #eiger4m = EigerTango('b303a/dia/eiger-4m', name='eiger4m', rotation=2)
    selunCZT = SelunTango('b303a/dia/selun', name='selunCZT', rotation=0, 
                          hdf_path='entry/instrument/Selun/data',)



    # The pandabox and some related pseudodetectors
    # Pandabox reading the LC400 encoders analog and controlling the fast shutter
    panda2 = PandaBox(name='panda2', host='b-nanomax-pandabox-2')

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
                                        'I0': 'a4'})

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
    for d in [panda2, pseudo, selunCZT]:
        d.active = True

    # define pre- and post-scan actions, per scan base class
    def pre_scan_stuff(slf):
        assert h5rec.is_alive(), 'hdf5 recorder is dead! this can''t be good. maybe restart contrast.'
        #runCommand('stoplive')
        #runCommand('optics on')
        #runCommand('fsopen')
        #basex.stop()   # making sure the base motor are not regulating
        #basey.stop()   # making sure the base motors are not regulating
        time.sleep(0.2)

    def post_scan_stuff(slf):
        #runCommand('fsclose')
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
