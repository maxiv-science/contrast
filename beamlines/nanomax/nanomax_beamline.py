"""
Sets up a some actual nanomax hardware.
"""

# need this main guard here because Process.start() (so our recorders)
# import __main__, and we don't want the subprocess to start new sub-
# processes etc.
if __name__=='__main__':

    import contrast
    from contrast.environment import env, runCommand
    from contrast.environment.data import SdmPathFixer
    from contrast.recorders import Hdf5Recorder, StreamRecorder
    from contrast.motors import DummyMotor, MotorMemorizer
    from contrast.motors.LC400 import LC400Motor
    from contrast.detectors.LC400Buffer import LC400Buffer
    from contrast.motors.TangoMotor import TangoMotor
    from contrast.motors.SmaractMotor import SmaractLinearMotor
    from contrast.motors.E727 import E727Motor
    from contrast.motors.KukaMotor import KukaRobot
    from contrast.detectors.Pilatus import Pilatus
    from contrast.detectors.Merlin import Merlin
    from contrast.detectors.Xspress3 import Xspress3
    from contrast.detectors.Ni6602 import Ni6602CounterCard
    from contrast.detectors.AdLink import AdLinkAnalogInput
    from contrast.detectors import Detector
    from contrast.detectors.DG645 import StanfordTriggerSource
    from nanomax_beamline_macros import *
    from NpointFlyscan import NpointFlyscan
    from macro_attenuate import *
    from contrast.scans import SoftwareScan, Ct
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

    # HACK! using sardana pseudomotors while figuring out how to do it properly
    seh_vo = TangoMotor(device='pseudomotor/seh_vg_ctrl/2', name='seh_vo', userlevel=1)
    seh_ho = TangoMotor(device='pseudomotor/seh_hg_ctrl/2', name='seh_ho', userlevel=1)
    seh_vg = TangoMotor(device='pseudomotor/seh_vg_ctrl/1', name='seh_vg', userlevel=1)
    seh_hg = TangoMotor(device='pseudomotor/seh_hg_ctrl/1', name='seh_hg', userlevel=1)

    # gap and taper
    ivu_gap = TangoMotor(device='g-v-csproxy-0:10000/r3-303l/id/idivu-01_gap', name='ivu_gap', userlevel=2, dial_limits=(4.5, 25), user_format='%.4f')
    ivu_taper = TangoMotor(device='g-v-csproxy-0:10000/r3-303l/id/idivu-01_taper', name='ivu_taper', userlevel=4, dial_limits=(-.05, .05))

    # other sardana motors
    mono_x2per = TangoMotor(device='b303a-o/opt/mono-perml', name='mono_x2per', userlevel=2, dial_limits=(-.1, .1))

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

    # KB mirror pitch piezos
    m1fpitch = E727Motor(device='B303A-EH/CTL/PZCU-01', axis=2, name='m1fpitch', userlevel=2, dial_limits=(0,30))
    m2fpitch = E727Motor(device='B303A-EH/CTL/PZCU-01', axis=3, name='m2fpitch', userlevel=2, dial_limits=(0,30))

    # Robot
    gamma, delta, radius = KukaRobot('B303-EH2/CTL/DM-02-ROBOT', names=['gamma', 'delta', 'radius'])

    # SSA through the Pool
    ssa_gapx = TangoMotor(device='B303A-O/opt/SLIT-01-GAPXPM', name='ssa_gapx', userlevel=2)
    ssa_gapy = TangoMotor(device='B303A-O/opt/SLIT-01-GAPYPM', name='ssa_gapy', userlevel=2)
    ssa_posx = TangoMotor(device='B303A-O/opt/SLIT-01-POSXPM', name='ssa_posx', userlevel=3)
    ssa_posy = TangoMotor(device='B303A-O/opt/SLIT-01-POSYPM', name='ssa_posy', userlevel=3)

    # microscope motors through the Pool
    oam_x = TangoMotor(device='b303a-e02/dia/om-01-x', name='oam_x', userlevel=4, user_format='%.4f', dial_format='%.4f')
    oam_y = TangoMotor(device='b303a-e02/dia/om-01-y', name='oam_y', userlevel=4, user_format='%.4f', dial_format='%.4f')
    oam_z = TangoMotor(device='b303a-e02/dia/om-01-z', name='oam_z', userlevel=4, user_format='%.4f', dial_format='%.4f')
    oam_zoom = TangoMotor(device='b303a-e02/dia/om-01-zoom', name='oam_zoom', userlevel=1)
    topm_x = TangoMotor(device='b303a-e02/dia/om-02-x', name='topm_x', userlevel=4, user_format='%.4f', dial_format='%.4f')
    topm_y = TangoMotor(device='b303a-e02/dia/om-02-y', name='topm_y', userlevel=4, user_format='%.4f', dial_format='%.4f')
    topm_z = TangoMotor(device='b303a-e02/dia/om-02-z', name='topm_z', userlevel=4, user_format='%.4f', dial_format='%.4f')
    topm_zoom = TangoMotor(device='b303a-e02/dia/om-02-zoom', name='topm_zoom', userlevel=1)

    # goniometer
    gontheta = TangoMotor(device='b303a-e02/dia/gon-01-theta', name='gontheta', userlevel=2)
    gonphi = TangoMotor(device='b303a-e02/dia/gon-01-phi', name='gonphi', userlevel=2)
    gonx1 = TangoMotor(device='b303a-e02/dia/gon-01-x1', name='gonx1', userlevel=4)
    gonx2 = TangoMotor(device='b303a-e02/dia/gon-01-x2', name='gonx2', userlevel=4)
    gonx3 = TangoMotor(device='b303a-e02/dia/gon-01-x3', name='gonx3', userlevel=4)
    gony1 = TangoMotor(device='b303a-e02/dia/gon-01-y1', name='gony1', userlevel=4)
    gony2 = TangoMotor(device='b303a-e02/dia/gon-01-y2', name='gony2', userlevel=4)
    gonz = TangoMotor(device='b303a-e02/dia/gon-01-z', name='gonz', userlevel=4)

    # beam stop motors
    bs_x = TangoMotor(device='B303A-E02/DIA/SAMS-01-X', name='bs_x', userlevel=4)
    bs_y = TangoMotor(device='B303A-E02/DIA/SAMS-01-Y', name='bs_y', userlevel=4)

    # some sardana pseudo motors - these are reimplemented but just need to be configured
    energy = TangoMotor(device='pseudomotor/nanomaxenergy_ctrl/1', name='energy')

    # some dummy motors
    dummy1 = DummyMotor(name='dummy1', userlevel=2)
    dummy2 = DummyMotor(name='dummy2', userlevel=2)

    # The delay generator as a software source for hardware triggers
    stanford = StanfordTriggerSource(name='stanford', device_name='B303A-A100380CAB03/CTL/DLY-01') 

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

    # a zmq recorder
    zmqrec = StreamRecorder(name='zmqrec')
#    zmqrec.start() # removed for now

    # add a memorizer so the motors keep their user positions and limits after a restart
    # note that this will overwrite the dial positions set above! delete the file to generate it again.
    memorizer = MotorMemorizer(name='memorizer', filepath='/data/visitors/nanomax/common/.memorizer')

    # deactivate all the detectors except pilatus as default
    for d in Detector.getinstances():
        d.active = False
    pilatus.active = True

    # define pre- and post-scan actions, per scan base class
    import PyTango
    import time
    def pre_scan_stuff(slf):
        runCommand('fsopen')
        time.sleep(1)
        runCommand('stoplive')
    def post_scan_stuff(slf):
        runCommand('fsclose')

    SoftwareScan._before_scan = pre_scan_stuff
    SoftwareScan._after_scan = post_scan_stuff
    Ct._before_ct = pre_scan_stuff
    Ct._after_ct = post_scan_stuff

    contrast.wisdom()
