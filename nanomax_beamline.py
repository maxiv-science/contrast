"""
Sets up a some actual nanomax hardware.
"""

# need this main guard here because Process.start() (so our recorders)
# import __main__, and we don't want the subprocess to start new sub-
# processes etc.
if __name__=='__main__':

    import lib
    from lib.environment import env
    from lib.recorders import Hdf5Recorder
    from lib.motors.E727 import E727Motor
    from lib.detectors import DetectorGroup
    from lib.detectors.Pilatus import Pilatus
    from lib.data import SdmPathFixer
    import os
    
    env.userLevel = 1 # we're not experts!

    samx = E727Motor(device='B303A-EH/CTL/PZCU-02', axis=1, name='samx')
    samy = E727Motor(device='B303A-EH/CTL/PZCU-02', axis=3, name='samy')
    samz = E727Motor(device='B303A-EH/CTL/PZCU-02', axis=2, name='samz')

    pilatus = Pilatus(name='pilatus', 
                      lima_device='lima/limaccd/b-nanomax-mobile-ipc-01',
                      det_device='lima/pilatus/b-nanomax-mobile-ipc-01')

    detgrp = DetectorGroup('detgrp')
    detgrp.append(pilatus)
    env.currentDetectorGroup = detgrp

    env.paths = SdmPathFixer('B303A/CTL/SDM-01')

    try:
        os.remove('/tmp/data.h5')
    except FileNotFoundError:
        pass
    h5rec = Hdf5Recorder('/tmp/data.h5', name='h5rec')
    h5rec.start()

