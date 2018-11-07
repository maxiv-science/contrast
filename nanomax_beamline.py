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
    from lib.motors import DummyMotor
    from lib.motors.E727 import E727Motor
    from lib.motors.SardanaPoolMotor import SardanaPoolMotor
    from lib.motors.SmaractMotor import SmaractLinearMotor
    from lib.detectors import DetectorGroup
    from lib.detectors.Pilatus import Pilatus
    from lib.data import SdmPathFixer
    import os
    
    env.userLevel = 1 # we're not experts!

    # sample piezos
    samx = E727Motor(device='B303A-EH/CTL/PZCU-02', axis=1, name='samx')
    samy = E727Motor(device='B303A-EH/CTL/PZCU-02', axis=3, name='samy')
    samz = E727Motor(device='B303A-EH/CTL/PZCU-02', axis=2, name='samz')
    samx.limits = (0, 100)
    samy.limits = (0, 100)
    samz.limits = (0, 100)

    # smaracts
    diode_x = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-04', axis=11, name='diode_x')

    # some steppers through sardana
    sams_x = SardanaPoolMotor(device='B303A-E02/DIA/SAMS-01-X', name='sams_x')
    sams_y = SardanaPoolMotor(device='B303A-E02/DIA/SAMS-01-Y', name='sams_y')
    sams_z = SardanaPoolMotor(device='B303A-E02/DIA/SAMS-01-Z', name='sams_z')
    sams_x.limits = (0, 25)
    sams_y.limits = (0, 25)
    sams_z.limits = (0, 25)

    # some sardana pseudo motors - these should really be reimplemented
    energy = SardanaPoolMotor(device='pseudomotor/nanomaxenergy_ctrl/1', name='energy')

    # some dummy motors
    dummy1 = DummyMotor(name='dummy1')
    dummy2 = DummyMotor(name='dummy2')

    # detectors
    pilatus = Pilatus(name='pilatus', 
                      lima_device='lima/limaccd/b-nanomax-mobile-ipc-01',
                      det_device='lima/pilatus/b-nanomax-mobile-ipc-01')

    # detector groups
    detgrp = DetectorGroup('detgrp')
    detgrp.append(pilatus)
    env.currentDetectorGroup = detgrp

    # the environment keeps track of where to write data
    env.paths = SdmPathFixer('B303A/CTL/SDM-01')

    # an hdf5 recorder
    h5rec = Hdf5Recorder(name='h5rec')
    h5rec.start()

