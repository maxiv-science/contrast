"""
Sets up a some actual nanomax hardware.
"""

# need this main guard here because Process.start() (so our recorders)
# import __main__, and we don't want the subprocess to start new sub-
# processes etc.
if __name__=='__main__':

    import lib
    from lib.environment import env
    from lib.environment.data import SdmPathFixer
    from lib.recorders import Hdf5Recorder
    from lib.motors import DummyMotor, MotorMemorizer
    from lib.motors.LC400 import LC400Motor
    from lib.detectors.LC400Buffer import LC400Buffer
    from lib.motors.TangoMotor import TangoMotor
    from lib.motors.SmaractMotor import SmaractLinearMotor
    from lib.detectors.Pilatus import Pilatus
    from lib.detectors.Merlin import Merlin
    from lib.detectors.Xspress3 import Xspress3
    from lib.detectors.Ni6602 import Ni6602CounterCard
    from lib.detectors.AdLink import AdLinkAnalogInput
    from lib.detectors import Detector
    import os
    
    env.userLevel = 1
    # chosen these levels here:
    # 1 - simple user
    # 2 - power user
    # 3 - optics
    # 4 - potentially dangerous

    # sample piezos
    sx = LC400Motor(device='B303A/CTL/PZCU-LC400', axis=2, name='sx', scaling=-1.0, dial_limits=(-50,50))
    sy = LC400Motor(device='B303A/CTL/PZCU-LC400', axis=3, name='sy', dial_limits=(-50,50))
    sz = LC400Motor(device='B303A/CTL/PZCU-LC400', axis=1, name='sz', scaling=-1.0, dial_limits=(-50,50))

    # base motors through sardana
    basex = TangoMotor(device='motor/icepap_ctrl_1_expert/16', name='basex', userlevel=1)
    basey = TangoMotor(device='motor/icepap_ctrl_1_expert/17', name='basey', userlevel=1)
    basez = TangoMotor(device='motor/icepap_ctrl_1_expert/18', name='basez', userlevel=1)

    # gap and taper
    ivu_gap = TangoMotor(device='g-v-csproxy-0:10000/r3-303l/id/idivu-01_gap', name='ivu_gap', userlevel=2, dial_limits=(4.5, 25))
    ivu_taper = TangoMotor(device='g-v-csproxy-0:10000/r3-303l/id/idivu-01_taper', name='ivu_taper', userlevel=4, dial_limits=(-.05, .05))

    # buffered position detector
    npoint_buff = LC400Buffer(device='B303A/CTL/FLYSCAN-02', name='npoint_buff', xaxis=2, yaxis=3, zaxis=1)
    npoint_buff.active = False # this can be switched on from flyscanning macros when needed, although it does no harm.

    # smaracts
    # controller 1
    skb_top = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-03', axis=0, name='skb_top', userlevel=2)
    skb_bottom = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-03', axis=1, name='skb_bottom', userlevel=2)
    skb_left = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-03', axis=2, name='skb_left', userlevel=2)
    skb_right = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-03', axis=3, name='skb_right', userlevel=2)
    kbfluox = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-03', axis=4, name='kbfluox', userlevel=3)
    # controller 2
    dbpm2_x = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-04', axis=0, name='dbpm2_x', userlevel=3)
    dbpm2_y = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-04', axis=1, name='dbpm2_y', userlevel=3)
    seh_top = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-04', axis=2, name='seh_top', userlevel=3)
    seh_bottom = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-04', axis=3, name='seh_bottom', userlevel=3)
    seh_left = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-04', axis=4, name='seh_left', userlevel=3)
    seh_right = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-04', axis=5, name='seh_right', userlevel=3)
    attenuator1_x = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-04', axis=6, name='attenuator1_x', userlevel=2)
    attenuator2_x = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-04', axis=7, name='attenuator2_x', userlevel=2)
    attenuator3_x = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-04', axis=8, name='attenuator3_x', userlevel=2)
    attenuator4_x = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-04', axis=9, name='attenuator4_x', userlevel=2)
    fastshutter_x = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-04', axis=10, name='fastshutter_x', userlevel=3)
    diode1_x = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-04', axis=11, name='diode1_x', userlevel=3)
    # controller 3
    diode2_y = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-05', axis=0, name='diode2_y', userlevel=3)
    diode2_z = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-05', axis=1, name='diode2_z', userlevel=3)
    diode2_x = SmaractLinearMotor(device='B303A-EH/CTL/PZCU-05', axis=2, name='diode2_x', userlevel=3)

    # SSA through the Pool
    ssa_gapx = TangoMotor(device='B303A-O/opt/SLIT-01-GAPXPM', name='ssa_gapx', userlevel=2)
    ssa_gapy = TangoMotor(device='B303A-O/opt/SLIT-01-GAPYPM', name='ssa_gapy', userlevel=2)
    ssa_posx = TangoMotor(device='B303A-O/opt/SLIT-01-POSXPM', name='ssa_posx', userlevel=3)
    ssa_posy = TangoMotor(device='B303A-O/opt/SLIT-01-POSYPM', name='ssa_posy', userlevel=3)

    # some sardana pseudo motors - these are reimplemented but just need to be configured
    energy = TangoMotor(device='pseudomotor/nanomaxenergy_ctrl/1', name='energy')

    # some dummy motors
    dummy1 = DummyMotor(name='dummy1', userlevel=2)
    dummy2 = DummyMotor(name='dummy2', userlevel=2)

    # detectors
    pilatus = Pilatus(name='pilatus', 
                      lima_device='lima/limaccd/b-nanomax-mobile-ipc-01',
                      det_device='lima/pilatus/b-nanomax-mobile-ipc-01')
    pilatus1m = Pilatus(name='pilatus1m',
                      lima_device='lima/limaccd/B-NANOMAX-PILATUS1M-IPC-01',
                      det_device='lima/pilatus/B-NANOMAX-PILATUS1M-IPC-01')
    merlin = Merlin(name='merlin',
                    lima_device='lima/limaccd/b303a-a100384-dia-detpicu-02',
                    det_device='lima/merlin/b303a-a100384-dia-detpicu-02')
    xspress3 = Xspress3(name='xspress3',
                        lima_device='lima/limaccd/b303a-a100380-dia-detxfcu-01',
                        det_device='lima/xspress3/b303a-a100380-dia-detxfcu-01')
    ni = Ni6602CounterCard(name='ni', device='B303A/CTL/NI6602-01')
    adlink = AdLinkAnalogInput(name='adlink', device='B303A-A100380/CTL/ADLINKAI-01')

    # the environment keeps track of where to write data
    env.paths = SdmPathFixer('B303A/CTL/SDM-01')

    # an hdf5 recorder
    h5rec = Hdf5Recorder(name='h5rec')
    h5rec.start()

    # add a memorizer so the motors keep their user positions and limits after a restart
    # note that this will overwrite the dial positions set above! delete the file to generate it again.
    memorizer = MotorMemorizer(name='memorizer', filepath='/data/visitors/nanomax/common/.memorizer')

    # deactivate all the detectors except pilatus as default
    for d in Detector.getinstances():
        d.active = False
    pilatus.active = True

