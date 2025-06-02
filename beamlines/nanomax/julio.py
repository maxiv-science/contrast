"""
The diffraction endstation at NanoMAX.
Simplified setup for Julio to test cont. neegy scanning
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
    from contrast.motors import DummyMotor
    from contrast.motors.TangoMotor import TangoMotor
    from contrast.detectors.Eiger import Eiger, EigerTango
    from contrast.detectors.AlbaEM import AlbaEM
    from contrast.detectors.PandaBox import PandaBox
    from contrast.detectors.PandaBox_PCAP import PandaBoxPCAP
    from contrast.detectors import Detector, PseudoDetector
    from contrast.detectors.epoch import Epoch
    from contrast.detectors.TangoAttributeDetector import TangoAttributeDetector
    from contrast.scans import SoftwareScan, Ct
    #from contrast.motors.EurothermDSMotor import EuroThermDSMotor #20240520 heater
    #from contrast.detectors.EurothermDSDetector import EuroThermDSDetector #20240520
    import macros_common
    import macros_diff
    import os
    import time

    # dissable ipython auto-completion/suggestions
    # taken from https://github.com/ipython/ipython/issues/13451#issuecomment-1014526360
    import IPython
    terminal = IPython.get_ipython()
    terminal.pt_app.auto_suggest = None

    env.userLevel = 4
    # arbitrarily chosen these levels:
    # 1 - simple user
    # 2 - power user
    # 3 - optics
    # 4 - potentially dangerous

    #######################################################################################################
    # Beamline equipment. Comment out when not used
    #######################################################################################################
    
    # gap and taper via a proxy in the local pool
    ivu_gap = TangoMotor(device='motor/ivu_gap_ctrl/1', name='ivu_gap', userlevel=2, dial_limits=(4.5, 25), user_format='%.4f')
    ivu_taper = TangoMotor(device='motor/ivu_taper_ctrl/1', name='ivu_taper', userlevel=4, dial_limits=(-.05, .05), user_format='%.4f')

    # Monochromator motors
    mono_bragg = TangoMotor(device='b303a-o/opt/MONO-BRAGML', name='mono_bragg', userlevel=4, dial_limits=(4.0, 27.46))

    # some sardana pseudo motors - these are reimplemented but just need to be configured
    energy_raw = TangoMotor(device='pseudomotor/nanomaxenergy_ctrl/1', name='energy_raw')
    energy = TangoMotor(device='pseudomotor/nanomaxenergy_corr_ctrl/1', name='energy')
    
    # some dummy motors
    dummy1 = DummyMotor(name='dummy1', userlevel=2)
    dummy2 = DummyMotor(name='dummy2', userlevel=2)

    #heater_motor = EuroThermDSMotor(device="B303A/DIA/TRC-01", name='heater_motor') #20240520 heater

    # The delay generator as a software source for hardware triggers
    # stanford = StanfordTriggerSource(name='stanford', device_name='B303A-A100380CAB03/CTL/DLY-01')

    # detectors
    epoch = Epoch(name='epoch')
    
    # eiger1m = Eiger(name='eiger1m', host='b-nanomax-eiger-1m-0')
    eiger1m = EigerTango('b303a/dia/eiger-1m', name='eiger1m', rotation = 0)
    #eiger500k = Eiger(name='eiger500k', host='b-nanomax-eiger-500k-0')
    eiger500k = EigerTango('b303a/dia/eiger-500k', name='eiger500k', rotation = 2)
    # Ion chamber at KB (Ch1), portable PIN diode (Ch3), PIN diode in DM4 (Ch4)
    alba2 = AlbaEM(name='alba2', host='b-nanomax-em2-2')

    # The pandabox and some related pseudodetectors
    panda0 = PandaBox(name='panda0', host='b-nanomax-pandabox-0')

    # setup of continous energy scanning
    panda1 = PandaBoxPCAP("b303a-a100380cab03/dia/panda-01", name='panda1', hdf_path='/entry/instrument/pandabox/data/')
    macros_common.EnergyFlyscan.PCAP=panda1
    macros_common.EnergyFlyscan.energy_motor=energy
    macros_common.EnergyFlyscan.ivu_gap_motor=ivu_gap
    macros_common.EnergyFlyscan.energyflyscan_panda = panda1
    macros_common.EnergyFlyscan.trigger_distribution_panda = panda0

    pseudo = PseudoDetector(name='pseudo',
                            variables={'c1': 'panda0/INENC1.VAL_Mean',
                                       'c2': 'panda0/INENC2.VAL_Mean',
                                       'c3': 'panda0/INENC3.VAL_Mean',
                                       # 'adc2': 'panda0/FMC_IN.VAL2_Mean',
                                       # 'adc3': 'panda0/FMC_IN.VAL3_Mean',
                                       # 'adc4': 'panda0/FMC_IN.VAL4_Mean',
                                       },
                            expression={'x': 'c2', 'y': 'c3', 'z': 'c1',
                                        # 'analog_x': '-adc2*5', 'analog_y': 'adc3*5', 'analog_z': '-adc1*5',
                                        # 'xbic': 'adc4',
                                        })
#                                        'analog_x': '-adc2*5*10/2**31', 'analog_y': 'adc3*5*10/2**31', 'analog_z': '-adc1*5*10/2**31'})

    
    # the environment keeps track of where to write data
    env.paths = PathFixer()
    env.paths.directory = '/data/staff/nanomax/commissioning_2025-1/20250512_Julio'

    # an hdf5 recorder
    h5rec = Hdf5Recorder(name='h5rec')
    h5rec.start()

    # a scicat recorder - paused until further notice
    scicatrec = ScicatRecorder(name='scicatrec', pathfixer='b303a-e02/ctl/sdm-01')
    scicatrec.start()

    # default detector selection
    for d in Detector.getinstances():
        d.active = False
    for d in [panda0, pseudo, alba2]:# :x3mini, eiger1m, ring_current, pilatus]:
        d.active = True
    #for d in [xspress3, eiger500k, eiger1m, pilatus, alba0, alba1, alba2]: 
    #    d.hw_trig = True

    # define pre- and post-scan actions, per scan base class
    def pre_scan_stuff(self):
        assert h5rec.is_alive(), 'hdf5 recorder is dead! this can''t be good. maybe restart contrast.'
        time.sleep(0.2)

    def post_scan_stuff(self):
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

    # chech git repo status at the start
    runCommand('checkgit')

    # contrast startup message with random acronym
    contrast.wisdom()
