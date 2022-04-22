"""
Sets up a Soft beamline with real motors and detectors.
"""
# need this main guard here because Process.start() (so our recorders)
# import __main__, and we don't want the subprocess to start new sub-
# processes etc.
if __name__=='__main__':

    import os
    import time
    import contrast
    import tango
    from contrast.environment import env
    from contrast.recorders import Hdf5Recorder, StreamRecorder
    from contrast.motors.TangoMotor import TangoMotor
    from contrast.detectors.PandaBoxSofti import PandaBoxSoftiPtycho, PandaBox0D
    from contrast.detectors import Detector, PseudoDetector
    from contrast.detectors.TangoAttributeDetector import TangoAttributeDetector
    from contrast.detectors.Andor3 import Andor3, AndorSofti
    from contrast.scans import SoftwareScan, Ct

    from contrast.motors import DummyMotor
    from contrast.detectors import DummyDetector

    sample_path = tango.DeviceProxy('B318A/CTL/SDM-01').Path
    
    env.userLevel = 5
    #env.paths.directory = '/data/staff/softimax/commissioning/andor_data/20211210'
    env.paths.directory = sample_path

    # the Hdf5Recorder later gets its path from the env object
    h5rec = Hdf5Recorder(name='h5rec')
    h5rec.start()

    # a zmq recorder
    #zmqrec = StreamRecorder(name='zmqrec')
    #zmqrec.start() # removed for now

    # motors
    finex = TangoMotor(device='PiezoPiE712/CTL/X', name='finex', user_format='%.3f', dial_format='%.3f', dial_limits=(0, 100), offset=50, scaling=-1)
    finey = TangoMotor(device='PiezoPiE712/CTL/Y', name='finey', user_format='%.3f', dial_format='%.3f', dial_limits=(0, 100), offset=50, scaling=-1)
    basex = DummyMotor(name='basex')
    # fine_dum = TangoMotor(device='B318A/CTL/DUMMY-01', name='fine_dum', user_format='%.3f', dial_format='%.3f', dial_limits=(0, 100))
    osax = TangoMotor(device='motor/osa_ctrl/1', name='osax', user_format='%.3f', dial_format='%.3f', offset=0.83)
    osay = TangoMotor(device='motor/osa_ctrl/2', name='osay', user_format='%.3f', dial_format='%.3f', offset=0.32)
    beamline_energy = TangoMotor(device='B318A/CTL/BEAMLINE-ENERGY', name='beamline_energy', user_format='%.3f', dial_format='%.3f', dial_limits=(275, 1600))

    # shutter = tango.DeviceProxy('B318A-EA01/CTL/GalilShutter')
    
    #finex = TangoMotor(device='B318A/CTL/DUMMY-01', name='finex', user_format='%.3f', dial_format='%.3f', dial_limits=(0, 100))
    #finey = TangoMotor(device='B318A/CTL/DUMMY-02', name='finey', user_format='%.3f', dial_format='%.3f', dial_limits=(0, 100))

    # detectors
    andor = AndorSofti(device='B318A-EA01/dia/andor-zyla-01', name='andor', frames_n=100)
    panda0 = PandaBoxSoftiPtycho(name='panda0', host='b-softimax-panda-0', frames_n=200)
    det1 = DummyDetector(name='det1')
    
    #panda0 = PandaBox0D(name='panda0', device='B318A-EA01/CTL/PandaPosTrig')
    abs_x = TangoAttributeDetector('abs_x', 'B318A-EA01/CTL/PandaPosTrig', 'AbsX')
    abs_y = TangoAttributeDetector('abs_y', 'B318A-EA01/CTL/PandaPosTrig', 'AbsY')
    roi = TangoAttributeDetector('roi', 'B318A-EA01/dia/andor-requests', 'data_mean')
    
    """ pseudo = PseudoDetector(name='pseudo',
                            variables={'enc_x':'panda0/INENC1.VAL_Value',
                                       'enc_y':'panda0/INENC2.VAL_Value',
                                       'c1':'panda0/COUNTER1.OUT_DIFF',
                                       'c2':'panda0/COUNTER2.OUT_DIFF',
                                       'c3':'panda0/COUNTER3.OUT_DIFF'},
                            expression={'x':'enc_x', 'y':'enc_z', 'count1':'c1', 'count2':'c2', 'count3':'c3'})
    diode = PandaBox0D(name='diode', type='diode')
    pmt = PandaBox0D(name='pmt', type='PMT') """

     # default detector selection
    for d in Detector.getinstances():
        d.active = False
    for d in [andor, panda0, roi, abs_x, abs_y]:
        d.active = True

    def pre_scan_stuff(slf):
            andor.stop()
            # shutter.Open()
            time.sleep(0.2)

    def post_scan_stuff(slf):
            pass
            # shutter.Close()

    SoftwareScan._before_scan = pre_scan_stuff
    SoftwareScan._after_scan = post_scan_stuff
    Ct._before_ct = pre_scan_stuff
    Ct._after_ct = post_scan_stuff

    contrast.wisdom()

    try:
        l = os.listdir(env.paths.directory)
        last = max([int(l_[:-3]) for l_ in l if (len(l_)==9 and l_.endswith('.h5'))])
        env.nextScanID = last + 1
        print('\nNote: inferring that the next scan number should be %u' % (last+1))
    except Exception as e:
        print(e)
