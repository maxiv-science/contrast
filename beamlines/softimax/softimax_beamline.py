"""
Sets up a Soft beamline with real motors and detectors.
"""
<<<<<<< HEAD

=======
>>>>>>> 4f5e4d32f874fc037da817934cc03039c43f478d
# need this main guard here because Process.start() (so our recorders)
# import __main__, and we don't want the subprocess to start new sub-
# processes etc.
if __name__=='__main__':

<<<<<<< HEAD
=======
    import os
>>>>>>> 4f5e4d32f874fc037da817934cc03039c43f478d
    import contrast
    from contrast.environment import env
    from contrast.recorders import Hdf5Recorder
    from contrast.motors.TangoMotor import TangoMotor
<<<<<<< HEAD
    from contrast.detectors.Andor3 import Andor3

    env.userLevel = 1 # we're not experts!
=======
    from contrast.detectors.PandaBoxSofti import PandaBoxSofti, PandaBox0D
    from contrast.detectors import Detector, PseudoDetector
    from contrast.detectors.Andor3 import Andor3

    env.userLevel = 5 # we're not experts!
>>>>>>> 4f5e4d32f874fc037da817934cc03039c43f478d
    env.paths.directory = '/tmp'

    # the Hdf5Recorder later gets its path from the env object
    h5rec = Hdf5Recorder(name='h5rec')
    h5rec.start()

    # motors
    finex = TangoMotor(device='PiezoPiE712/CTL/X', name='finex', user_format='%.3f', dial_format='%.3f', dial_limits=(0, 100))
    finey = TangoMotor(device='PiezoPiE712/CTL/Y', name='finey', user_format='%.3f', dial_format='%.3f', dial_limits=(0, 100))

    # detectors
    andor = Andor3(device='b318a/andor3device/test', name='andor')
<<<<<<< HEAD

    contrast.wisdom()
=======
    panda0 = PandaBoxSofti(name='panda0')
    pseudo = PseudoDetector(name='pseudo',
                            variables={'enc_x':'panda0/INENC1.VAL_Value',
                                       'enc_y':'panda0/INENC2.VAL_Value',
                                       'c1':'panda0/COUNTER1.OUT_DIFF',
                                       'c2':'panda0/COUNTER2.OUT_DIFF',
                                       'c3':'panda0/COUNTER3.OUT_DIFF'},
                            expression={'x':'enc_x', 'y':'enc_z', 'count1':'c1', 'count2':'c2', 'count3':'c3'})
    diode = PandaBox0D(name='diode', type='diode')
    pmt = PandaBox0D(name='pmt', type='PMT')

     # default detector selection
    for d in Detector.getinstances():
        d.active = False
    for d in [diode, pmt]:
        d.active = True

    contrast.wisdom()

    try:
        l = os.listdir(env.paths.directory)
        last = max([int(l_[:-3]) for l_ in l if (len(l_)==9 and l_.endswith('.h5'))])
        env.nextScanID = last + 1
        print('\nNote: inferring that the next scan number should be %u' % (last+1))
    except Exception as e:
        print(e)
>>>>>>> 4f5e4d32f874fc037da817934cc03039c43f478d
