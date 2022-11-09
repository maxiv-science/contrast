"""
Sets up a mock beamline with dummy motors and detectors.
"""

# need this main guard here because Process.start() (so our recorders)
# import __main__, and we don't want the subprocess to start new sub-
# processes etc.
if __name__ == '__main__':

    import contrast
    from contrast.motors import DummyMotor, MotorMemorizer, ExamplePseudoMotor
    from contrast.scans import *
    from contrast.detectors import (DummyDetector, Dummy1dDetector,
                                    DummyWritingDetector,
                                    DummyWritingDetector2)
    from contrast.detectors.Andor3 import Andor3
    from contrast.motors.TangoMotor import TangoMotor
    from contrast.environment import env, register_shortcut
    from contrast.recorders import Hdf5Recorder, StreamRecorder
    import os

    # if you have ptypy installed, you can generate mock ptycho data
    # from sim_ptycho_scan import *

    env.userLevel = 1  # we're not experts!

    basex = DummyMotor(name='basex')
    basex.dial_limits = (-8000, 8000)
    basex.velocity = 10000
    basey = DummyMotor(name='basey')
    basey.dial_limits = (-8000, 8000)
    basey.velocity = 10000
    basez = DummyMotor(name='basez')
    basez.dial_limits = (-8000, 8000)
    basez.velocity = 10000

    sx = DummyMotor(name='sx')
    sx.dial_limits = (-50, 50)
    sx.velocity = 100
    sy = DummyMotor(name='sy')
    sy.dial_limits = (-50, 50)
    sy.velocity = 100
    sz = DummyMotor(name='sz')
    sz.dial_limits = (-50, 50)
    sz.velocity = 100

    energy = DummyMotor(name='energy')
    energy.dial_limits = (5000, 35000)
    energy.velocity = 50000
    energy.dial_position = 10000

    attenuator1_x = DummyMotor(name='attenuator1_x')
    attenuator2_x = DummyMotor(name='attenuator2_x')
    attenuator3_x = DummyMotor(name='attenuator3_x')
    attenuator4_x = DummyMotor(name='attenuator4_x')
    attenuator1_x.dial_limits = (-42000, 42000)
    attenuator2_x.dial_limits = (-42000, 42000)
    attenuator3_x.dial_limits = (-42000, 42000)
    attenuator4_x.dial_limits = (-42000, 42000)
    attenuator1_x.velocity = 20000
    attenuator2_x.velocity = 20000
    attenuator3_x.velocity = 20000
    attenuator4_x.velocity = 20000

    gap = DummyMotor(name='gap', userlevel=5, user_format='%.5f')

    diff = ExamplePseudoMotor([basex, basey], name='diff')

    #det1 = DummyDetector(name='det1')
    #det2 = DummyWritingDetector(name='det2')
    #det3 = Dummy1dDetector(name='det3')
    #det4 = DummyWritingDetector2(name='det4')

    # andor = Andor3(name='andor', device='zyla/test/1') # inital test
	andor = Andor3(name='andor', device='b303a-e01/dia/zyla')
    #andor.proxy.rotation=1
    #andor.proxy.flipud=True
	#andor.proxy.fliplr=True

    env.paths.directory = '/data/staff/nanomax/commissioning_2022-2/20221107_DESY_Andor_test/raw/sample/'

    # the Hdf5Recorder later gets its path from the env object
    h5rec = Hdf5Recorder(name='h5rec')
    h5rec.start()

    # a zmq recorder
    zmqrec = StreamRecorder(name='zmqrec')
    zmqrec.start()

    # this MotorMemorizer keeps track of motor user positions and
    # limits, and dumps this to file when they are changed.
    memorizer = MotorMemorizer(
        name='memorizer', filepath='/tmp/.dummy_beamline_motors')

    # handy shortcuts
    register_shortcut('wsample', 'wm samx samy')
    register_shortcut('waaa', 'wa')
    register_shortcut('zero_sample', 'umv samx 0 samy 0')

    # define pre- and post-scan actions, per base class
    def pre_scan_stuff(slf):
        print("Maybe open a shutter here?")

    def post_scan_stuff(slf):
        print("Maybe close that shutter again?")

    SoftwareScan._before_scan = pre_scan_stuff
    SoftwareScan._after_scan = post_scan_stuff
    Ct._before_ct = pre_scan_stuff
    Ct._after_ct = post_scan_stuff

    contrast.wisdom()
