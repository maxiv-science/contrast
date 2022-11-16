from contrast.motors import DummyMotor, MotorMemorizer, ExamplePseudoMotor
from contrast.detectors import (DummyDetector, Dummy1dDetector,
                                DummyWritingDetector,
                                DummyWritingDetector2)
from contrast.recorders import Hdf5Recorder, StreamRecorder


samx = DummyMotor(name='samx')
samx.dial_limits = (0, 10)

samy = DummyMotor(name='samy')
samy.dial_limits = (-5, 5)

samr = DummyMotor(name='samr')
samr.dial_limits = (-180, 180)
samr.velocity = 30

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
sy = DummyMotor(name='sy')
sy.dial_limits = (-50, 50)
sz = DummyMotor(name='sz')
sz.dial_limits = (-50, 50)
sr = DummyMotor(name='sr')
sr.dial_limits = (-180, 180)
sr.velocity = 30

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

diff = ExamplePseudoMotor([samx, samy], name='diff')

det1 = DummyDetector(name='det1')
det2 = DummyWritingDetector(name='det2')
det3 = Dummy1dDetector(name='det3')
det4 = DummyWritingDetector2(name='det4')

# this MotorMemorizer keeps track of motor user positions and
# limits, and dumps this to file when they are changed.
memorizer = MotorMemorizer(
    name='memorizer', filepath='/tmp/.dummy_beamline_motors')

h5rec = Hdf5Recorder(name='h5rec')
h5rec.start()

# zmqrec = StreamRecorder(name='zmqrec')
# zmqrec.start()
