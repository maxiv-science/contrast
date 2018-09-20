from .Recorder import Recorder, DummyRecorder, active_recorders
try:
    from .PlotRecorder import PlotRecorder
except ImportError:
    print('Note: PlotRecorder not available, probably because matplotlib is missing.')

from .Hdf5Recorder import Hdf5Recorder
