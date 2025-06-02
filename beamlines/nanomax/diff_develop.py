"""
The diffraction endstation at NanoMAX.
"""

# need this main guard here because Process.start() (so our recorders)
# import __main__, and we don't want the subprocess to start new sub-
# processes etc.
if __name__ == '__main__':
    import contrast
    from contrast.environment import env, runCommand
    from contrast.environment.data import SdmPathFixer, PathFixer
    from contrast.environment.scheduling import MaxivScheduler
    from contrast.recorders import Hdf5Recorder, StreamRecorder, ScicatRecorder
    from contrast.motors import DummyMotor, MotorMemorizer
    from contrast.motors.LC400 import LC400Motor
    from contrast.detectors.LC400Buffer import LC400Buffer
    from contrast.motors.TangoMotor import TangoMotor
    from contrast.motors.TangoAttributeMotor import TangoAttributeMotor
    from contrast.motors.SmaractMotor import SmaractLinearMotor
    from contrast.motors.SmaractMotor import SmaractRotationMotor
    from contrast.motors.E727 import E727Motor
    from contrast.motors.PiezoLegsMotor import PiezoLegsMotor
    from contrast.motors.KukaMotor import KukaRobot
    from contrast.detectors.Pilatus import Pilatus2, Pilatus3
    from contrast.detectors.Merlin import Merlin
    from contrast.detectors.Xspress3 import Xspress3
    from contrast.detectors.Andor3 import Andor3
    from contrast.detectors.Eiger import Eiger, EigerTango
    from contrast.detectors.AlbaEM import AlbaEM
    from contrast.detectors.PandaBox import PandaBox
    from contrast.detectors.xandy import Xandy
    from contrast.detectors import Detector, PseudoDetector
    from contrast.detectors.DG645 import StanfordTriggerSource
    from contrast.detectors.Keysight import Keysight2985
    from contrast.detectors.epoch import Epoch
    from contrast.detectors.BaslerCamera import BaslerCamera
    from contrast.detectors.TangoAttributeDetector import TangoAttributeDetector
    from contrast.scans import SoftwareScan, Ct
    import macros_common
    import macros_diff
    import os
    import time

    env.userLevel = 2
    # arbitrarily chosen these levels:
    # 1 - simple user
    # 2 - power user
    # 3 - optics
    # 4 - potentially dangerous

    # sample piezos
    #sx = LC400Motor(device='B303A/CTL/PZCU-LC400B', axis=2, name='sx', scaling=-1.0, dial_limits=(-50,50), user_format='%.3f')
    #sy = LC400Motor(device='B303A/CTL/PZCU-LC400B', axis=3, name='sy', dial_limits=(-50,50), user_format='%.3f')
    #sz = LC400Motor(device='B303A/CTL/PZCU-LC400B', axis=1, name='sz', scaling=-1.0, dial_limits=(-50,50), user_format='%.3f')

    # # base motors using PMD301 controller
    #basex = PiezoLegsMotor(device='B303A-EH/CTL/PZCU-08', axis=0, name='basex', userlevel=1,
     #                      scaling=-1e-3, velocity=200, offset=+23735.076, dial_limits=(13734076, 33736076), user_format='%.3f', dial_format='%.0f')
#    basey = PiezoLegsMotor(device='B303A-EH/CTL/PZCU-08', axis=1, name='basey', userlevel=1,
#                           scaling=+1e-3, velocity=200, offset=-25102.563, dial_limits=(15101563, 35103563) ,user_format='%.3f', #dial_format='%.0f')
#    basez = PiezoLegsMotor(device='B303A-EH/CTL/PZCU-08', axis=2, name='basez', userlevel=1,
#                           scaling=-1e-3, velocity=200, offset=+24346.752, dial_limits=(14345752, 34247752), user_format='%.3f', #dial_format='%.0f') 
    

    # # goniometer
    # gontheta = TangoMotor(device='b303a-e02/dia/gon-01-theta', name='gontheta', userlevel=2, user_format='%.4f', dial_format='%.4f')
    # gonphi = TangoMotor(device='b303a-e02/dia/gon-01-phi', name='gonphi', userlevel=2, user_format='%.4f', dial_format='%.4f')

    dbpm1_x = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-07', axis=1, name='dbpm1_x', userlevel=6, frequency=1000)
    dbpm1_y = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-07', axis=2, name='dbpm1_y', userlevel=6, frequency=1000)

    # # some sardana pseudo motors - these are reimplemented but just need to be configured
    # energy_raw = TangoMotor(device='pseudomotor/nanomaxenergy_ctrl/1', name='energy_raw')
    # energy = TangoMotor(device='pseudomotor/nanomaxenergy_corr_ctrl/1', name='energy')

    # # some dummy motors
    # dummy1 = DummyMotor(name='dummy1', userlevel=2)
    # dummy2 = DummyMotor(name='dummy2', userlevel=2)

    # # detectors
    #epoch = Epoch(name='epoch')
    # pilatus = Pilatus3('b303a/dia/pilatus', name='pilatus')
    merlin = Merlin(name='merlin', host='localhost')
    # # xspress3 = Xspress3(name='xspress3', device='staff/alebjo/xspress3')
    
    # eiger1m = Eiger(name='eiger1m', host='b-nanomax-eiger-1m-0', hdf_path='entry/instrument/Eiger/data')
    # eiger500k = Eiger(name='eiger500k', host='b-nanomax-eiger-500k-0')
    #eiger = EigerTango('b303a/dia/eiger-500k', name='eiger')
    #alba0 = AlbaEM(name='alba0', host='b-nanomax-em2-0')
    #alba2 = AlbaEM(name='alba2', host='b-nanomax-em2-2')
    
    #The keysight as both     from contrast.detectors.Keysight import Keysight2985a detector (ammeter) and motor (bias voltage)
    # keysight = Keysight2985(name='keysight', device='B303A-EH/CTL/KEYSIGHT-01')
    # keysight_bias = TangoAttributeMotor(name='keysight_bias', device='B303A-EH/CTL/KEYSIGHT-01', attribute='bias_voltage',    dial_limits=(-10,10))
    # keysight_range = TangoAttributeMotor(name='keysight_range', device='B303A-EH/CTL/KEYSIGHT-01', attribute='current_range', dial_format='%E', user_format='%E')

    # CIVIDEC XandY
    # xandy = Xandy(name="xandy", host='b-nanomax-user-devices-0')
    # The pandabox and some related pseudodetectors
    #panda0 = PandaBox(name='panda0', host='b-nanomax-pandabox-0')
    #macros_common.NpointFlyscan.panda = panda0
    #pseudo = PseudoDetector(name='pseudo',
    #                       variables={'c1': 'panda0/INENC1.VAL_Mean',
    #                                  'c2': 'panda0/INENC2.VAL_Mean',
    #                                  'c3': 'panda0/INENC3.VAL_Mean',
    #                                  'adc1': 'panda0/FMC_IN.VAL1_Mean',
    #                                  'adc2': 'panda0/FMC_IN.VAL2_Mean',
    #                                  'adc3': 'panda0/FMC_IN.VAL3_Mean',
    #                                  'adc4': 'panda0/FMC_IN.VAL4_Mean'},
    #                       expression={'x': 'c2', 'y': 'c3', 'z': 'c1',
    #                                  'analog_x': '-adc2*5', 'analog_y': 'adc3*5', 'analog_z': '-adc1*5',})

    # the environment keeps track of where to write data
    # env.paths = SdmPathFixer('B303A-E02/CTL/SDM-01')
    env.paths = PathFixer()

    # an hdf5 recorder
    h5rec = Hdf5Recorder(name='h5rec')
    h5rec.start()

    # # a zmq recorder
    # zmqrec = StreamRecorder(name='zmqrec')
    # zmqrec.start()

    # default detector selection
    for d in Detector.getinstances():
        d.active = False
    #for d in [panda0, pseudo, eiger]: #pilatus]: #, ring_current]: #, eiger1m]:
    #    d.active = True

    # define pre- and post-scan actions, per scan base class
    # def pre_scan_stuff(slf):
    #    assert h5rec.is_alive(), 'hdf5 recorder is dead! this can''t be good. maybe restart contrast.'
    #    basex.stop()   # making sure the base motor are not regulating
    #    basey.stop()   # making sure the base motor are not regulating
    #    basez.stop()   # making sure the base motor are not regulating
    #    time.sleep(0.2)

    # def post_scan_stuff(slf):
    #    pass

    # SoftwareScan._before_scan = pre_scan_stuff
    # SoftwareScan._after_scan = post_scan_stuff
    # Ct._before_ct = pre_scan_stuff
    # Ct._after_ct = post_scan_stuff

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

