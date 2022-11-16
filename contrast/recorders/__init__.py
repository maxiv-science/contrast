"""
Provides the ``Recorder`` base class as well as recorder subclasses for
writing, streaming and plotting data.
"""

import os
import signal
import atexit
from .Recorder import Recorder, DummyRecorder, active_recorders
from .Recorder import RecorderHeader, RecorderFooter
try:
    from .PlotRecorder import PlotRecorder
except ImportError:
    print('Note: PlotRecorder not available, probably because matplotlib '
          + 'is missing.')

try:
    from .Hdf5Recorder import Hdf5Recorder
except ImportError:
    print('Note: Hdf5Recorder not available, probably because h5py is '
          + 'missing.')

try:
    from .StreamRecorder import StreamRecorder
except ImportError:
    print('Note: StreamRecorder not available, probably because zmq is '
          + 'missing.')

try:
    from .ScicatRecorder import ScicatRecorder
except ImportError:
    print('Note: ScicatRecorder not available, probably because the MAX IV '
          + 'helper library scifish is missing.')


def kill_all_recorders():
    for r in Recorder.getinstances():
        print("Killing %s" % r.name)
        os.kill(r.pid, signal.SIGTERM)


atexit.register(kill_all_recorders)
