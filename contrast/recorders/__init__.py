from .Recorder import Recorder, DummyRecorder, active_recorders, RecorderHeader, RecorderFooter
try:
    from .PlotRecorder import PlotRecorder
except ImportError:
    print('Note: PlotRecorder not available, probably because matplotlib is missing.')

try:
    from .Hdf5Recorder import Hdf5Recorder
except ImportError:
    print("Note: Hdf5Recorder not available, probably because h5py is missing.")

