from . import Recorder
import h5py
import time
import numpy as np

class Hdf5Recorder(Recorder):
    """
    Since recorders run in separate processes, you can't interact with
    them other than through the queue. Therefore, changing hdf5 file
    means closing the recorder and opening a new one.
    """
    def __init__(self, filename, name='hdf5recorder',
                       close_file_after=600, flush_file_after=5):
        Recorder.__init__(self, name=name)
        self.filename = filename
        self.fp = None
        self.file_open = False
        self.last_data = time.time()
        self.last_flush = time.time()
        self.close_file_after = close_file_after
        self.flush_file_after = flush_file_after

    def _open(self):
        self.fp = h5py.File(self.filename, 'a')
        self.file_open = True

    def _close(self):
        try:
            self.fp.flush()
            self.fp.close()
            self.file_open = False
        except (ValueError, AttributeError):
            pass

    def init(self):
        self.scannr = None
        self._open()

    def act_on_data(self, dct):
        """
        Write data packets to the h5 file.
        """
        if not self.file_open:
            self._open()
        self.last_data = time.time()
        entry = 'entry%d/' % dct['scannr']
        base = entry + 'measurement/'
        for key, val in dct.items():
            name = base + key
            if not dct['scannr'] == self.scannr:
                # a new scan, so prepare new datasets!
                if name in self.fp:
                    print('************ WARNING ************')
                    print('Data already exists! Hdf5Recorder')
                    print('won''t write data to this target.')
                    print('*********************************')
                    return
                if isinstance(val, np.ndarray):
                    # arrays
                    d = self.fp.create_dataset(name, shape=(1,)+val.shape, maxshape=(None,)+val.shape, dtype=val.dtype)
                elif (type(val) == str) or hasattr(val, 'target'):
                    # strings or links
                    d = self.fp.create_dataset(name, shape=(1,), maxshape=(None,), dtype='S100')
                else:
                    # scalars of any type
                    d = self.fp.create_dataset(name, shape=(1,), maxshape=(None,), dtype=type(val))
            else:
                # existing scan, just resize and add data
                d = self.fp[name]
                d.resize((d.shape[0]+1,) + d.shape[1:])

            # special cases
            if type(val) == str:
                # a string
                val_ = val.encode(encoding='ascii', errors='ignore')
            elif hasattr(val, 'target'):
                # a link
                val_ = val.target.encode(encoding='ascii', errors='ignore')
            else:
                val_ = val
            d[-1] = val_
        self.scannr = dct['scannr']

    def periodic_check(self):
        if not self.file_open:
            return
        t = time.time()
        if t - self.last_data > self.close_file_after:
            self._close()
        elif t - self.last_flush > self.flush_file_after:
            self.fp.flush()
            self.last_flush = t

    def close(self):
        self._close()
