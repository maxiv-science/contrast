from .Recorder import Recorder, DummyRecorder, active_recorders, RecorderHeader, RecorderFooter
try:
    from .PlotRecorder import PlotRecorder
except ImportError:
    print('Note: PlotRecorder not available, probably because matplotlib is missing.')

try:
    from .Hdf5Recorder import Hdf5Recorder
except ImportError:
    print("Note: Hdf5Recorder not available, probably because h5py is missing.")

import os, signal
def kill_all_recorders():
    for r in Recorder.getinstances():
        print("Killing %s" % r.name)
        os.kill(r.pid, signal.SIGTERM)

import atexit
atexit.register(kill_all_recorders)
