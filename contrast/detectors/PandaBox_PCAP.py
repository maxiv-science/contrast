from .Detector import Detector
from ..environment import env
from ..recorders.Hdf5Recorder import Link
import os
import time
import tango




class PandaBoxPCAP(Detector):
    """
    Basic class for reading the PCAP from a PandaBox via a Tango Device as a detector.
    This class works with tango device servers based on https://gitlab.maxiv.lu.se/kits-maxiv/dev-maxiv-nanomaxpandabox
    The results are written to a HDF5 file by the device server. Contrast links to the written HDF5 file.
    """

    def __init__(self, device_name, hdf_path='entry/', **kwargs):
        super(PandaBoxPCAP,self).__init__(**kwargs)

        self._hdf_path = hdf_path

        self.proxy = tango.DeviceProxy(device_name)


    
    def prepare(self, acqtime, dataid, n_starts):
        
        self.n_started = 0
        self.n_starts = n_starts
        if self.busy():
            raise Exception(f'{self.name} is busy!')

        if (dataid is None) or (env.paths.directory is None):
            # no saving
            # Tango server requires a valid path, even if data is not saved
            self.saving_file = '/dev/null'
        else:
            # saving
            path = env.paths.directory
            # FIXME change to .hdf5 once Tnago Server is fixed
            fn = f'scan_{dataid:06d}_{self.name}.h5'
            self.saving_file = os.path.join(path, fn)
            if os.path.exists(self.saving_file):
                print('%s: this hdf5 file exists, I am raising an error now'
                      % self.name)
                raise Exception('%s hdf5 file already exists' % self.name)
        self.proxy.DestinationFilename = self.saving_file


    def arm(self):
        pass

    def start(self):
        """
        Start acquisition for any software triggered detectors.
        """
        self.proxy.Arm()

    def initialize(self):
        self.n_started = 0

    def stop(self):
        self.proxy.Disarm()
        self.n_started = 0

    def busy(self):
        if self.proxy.State() == tango.DevState.RUNNING:
            if hasattr(self, 'n_starts') and self.n_starts == self.proxy.nFramesReceived:
                self.proxy.Disarm()
            return True
        else:
            return False

    def read(self):
        if self.saving_file == '':
            return None
        else:
            return {'energy': Link(self.saving_file, self._hdf_path,
                                   universal=True)
                                   }
