"""
Minimal beamline configuration for testing real time ptycho
at NanoMAX. Also provides simulated dummy ptycho data.
"""

if __name__=='__main__':

    import contrast
    from contrast.recorders import StreamRecorder
    from contrast.detectors.SimplePilatus import SimplePilatus
    from contrast.motors.LC400 import LC400Motor
    from dummy_ptycho import *

    # a zmq recorder
    zmqrec = StreamRecorder(name='zmqrec')
    zmqrec.start()

    # detector
    pilatus_test = SimplePilatus(name='pilatus_test', devname='test/alebjo/pilatusproxy')

    # motors
    sx = LC400Motor(device='B303A/CTL/PZCU-LC400', axis=2, name='sx', scaling=-1.0, dial_limits=(-50,50))
    sy = LC400Motor(device='B303A/CTL/PZCU-LC400', axis=3, name='sy', dial_limits=(-50,50))

    contrast.wisdom()
