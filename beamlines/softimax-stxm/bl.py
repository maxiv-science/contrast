from contrast.motors import DummyMotor
from contrast.recorders import Hdf5Recorder, DummyRecorder
from dummy_detector import DummyStxmDetector
from dummy_scan import StxmScan
from contrast.environment import env
import os


finex = DummyMotor(name='finex', dial_limits=(-50, 50), velocity=500)
finey = DummyMotor(name='finey', dial_limits=(-50, 50), velocity=500)

coarsex = DummyMotor(name='coarsex', dial_limits=(50, 1024 - 50), velocity=5000)
coarsey = DummyMotor(name='coarsey', dial_limits=(50, 768 - 50), velocity=5000)

energy = DummyMotor(name='energy', dial_limits=(300, 1000), velocity=100,
                    dial_position=500)

h5rec = Hdf5Recorder(name='h5rec')
h5rec.start()

dummyrec = DummyRecorder(name='dummyrec')
dummyrec.start()

stxm_det = DummyStxmDetector(name='stxm_det',
                             motors=[coarsex, coarsey, finex, finey, energy])

# set path and remove any h5 files there
env.paths.directory = '/tmp'
fns = [fn for fn in os.listdir('/tmp') if fn.endswith('.h5')]
[os.remove('/tmp/%s' % fn) for fn in fns]
