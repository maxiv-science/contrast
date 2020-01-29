from . import Recorder
import h5py
import time
import numpy as np
import os

class Link(h5py.ExternalLink):
    """
    Helper class which wraps a h5py.ExternalLink, but which also
    informs the Hdf5Recorder about whether there will be one link per
    scan (universal=True) or one link per position (universal=False).
    """
    def __init__(self, *args, universal=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.universal = universal

class Hdf5Recorder(Recorder):
    """
    Recorder which writes to hdf5 files.
    """
    def __init__(self, name=None):
        Recorder.__init__(self, name=name)
        self.fp = None

    def act_on_header(self, dct):
        """
        Opens a file when a new scan starts.
        """
        filename = os.path.join(dct['path'], '%06u.h5'%dct['scannr'])
        if os.path.isfile(filename):
            print('************ WARNING ************')
            print('Data already exists! Hdf5Recorder')
            print('won''t write data to this target.')
            print('*********************************')
            self.fp = None
        else:
            self.fp = h5py.File(filename, 'w')
            self.act_on_data({'snapshot':dct['snapshot']}, base='entry/')
            self.act_on_data({'description':dct['description']}, base='entry/')

    def act_on_data(self, dct, base='entry/measurement/'):
        """
        Write data packets to the h5 file.
        """
        if self.fp is None:
            print('** no hdf5 file open, so not writing anything')
            return
        for key, val in dct.items():
            name = base + key

            # allow Nones:
            if val is None:
                val = 'None'

            # treat dict values recursively
            if type(val) == dict:
                new_dct = {key + '/' + str(k): v for k, v in val.items()}
                self.act_on_data(new_dct, base=base)
                continue

            # all other data types
            create = name not in self.fp
            if isinstance(val, np.ndarray):
                # arrays are stacked along the first index
                if create:
                    d = self.fp.create_dataset(name, shape=val.shape, maxshape=(None,)+val.shape[1:], dtype=val.dtype)
                    old = 0
                else:
                    d = self.fp[name]
                    old = d.shape[0]
                    d.resize((old+val.shape[0],) + d.shape[1:])
                d[old:] = val

            elif isinstance(val, h5py.ExternalLink):
                # links
                try:
                    universal = val.universal
                except AttributeError:
                    universal = False
                # we need relative paths
                val = h5py.ExternalLink(
                    filename=os.path.relpath(val.filename, start=os.path.dirname(self.fp.filename)),
                    path=val.path)
                if create:
                    if universal:
                        self.fp[name] = val
                    else:
                        d = self.fp.create_group(name)
                if not universal:
                    d = self.fp[name]
                    link_key = '%06u' % len(d.keys())
                    d[link_key] = val

            elif isinstance(val, h5py.VirtualLayout):
                # layout for a virtual dataset
                if create:
                    self.fp.create_virtual_dataset(name, val, fillvalue=-1)

            elif (type(val) == str):
                # strings
                if create:
                    d = self.fp.create_dataset(name, shape=(0,), maxshape=(None,), dtype='S100')
                else:
                    d = self.fp[name]
                val = val.encode(encoding='ascii', errors='ignore')
                d.resize((d.shape[0]+1,) + d.shape[1:])
                d[-1] = val

            else:
                # scalars of any type
                if create:
                    d = self.fp.create_dataset(name, shape=(0,), maxshape=(None,), dtype=type(val))
                else:
                    d = self.fp[name]
                d.resize((d.shape[0]+1,) + d.shape[1:])
                d[-1] = val                


    def act_on_footer(self, dct):
        """
        Closes the file after the scan.
        """
        if self.fp is not None:
            self.fp.flush()
            self.fp.close()
