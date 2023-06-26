"""
Provides the ``Recorder`` base class as well as recorder subclasses for
writing, streaming and plotting data.
"""

import os
import signal
import atexit
from .Recorder import Recorder, DummyRecorder, active_recorders
from .Recorder import RecorderHeader, RecorderFooter
from .PlotRecorder import PlotRecorder
from .Hdf5Recorder import Hdf5Recorder
from .StreamRecorder import StreamRecorder
from .ScicatRecorder import ScicatRecorder


def kill_all_recorders():
    for r in Recorder.getinstances():
        print("Killing %s" % r.name)
        os.kill(r.pid, signal.SIGTERM)


atexit.register(kill_all_recorders)
