"""
Sets up a Soft beamline with real motors and detectors.
"""

# need this main guard here because Process.start() (so our recorders)
# import __main__, and we don't want the subprocess to start new sub-
# processes etc.
if __name__=='__main__':

    import contrast
    from contrast.environment import env
    from contrast.recorders import Hdf5Recorder
    from contrast.motors.TangoMotor import TangoMotor
    from contrast.detectors.Andor3 import Andor3

    env.userLevel = 1 # we're not experts!
    env.paths.directory = '/tmp'

    # the Hdf5Recorder later gets its path from the env object
    h5rec = Hdf5Recorder(name='h5rec')
    h5rec.start()

    # motors
    finex = TangoMotor(device='PiezoPiE712/CTL/X', name='finex', user_format='%.3f', dial_format='%.3f', dial_limits=(0, 100))
    finey = TangoMotor(device='PiezoPiE712/CTL/Y', name='finey', user_format='%.3f', dial_format='%.3f', dial_limits=(0, 100))

    # detectors
    andor = Andor3(device='b318a/andor3device/test', name='andor')

    contrast.wisdom()
