from .Detector import Detector, SoftwareLiveDetector, TriggeredDetector, BurstDetector
from ..environment import env
from ..recorders.Hdf5Recorder import Link
import os

try:
    import PyTango
except ModuleNotFoundError:
    pass

class Pilatus(Detector, SoftwareLiveDetector, TriggeredDetector, BurstDetector):
    """
    Detector class interfacing with the Tango device from pilatus-streamer:

    https://gitlab.maxiv.lu.se/nanomax-beamline/pilatus-streamer
    """
    

    def __init__(self, name=None, device=None):
        self.device_name = device
        BurstDetector.__init__(self)
        SoftwareLiveDetector.__init__(self)
        TriggeredDetector.__init__(self)
        Detector.__init__(self, name=name) # last so that initialize() can overwrite parent defaults
        self._hdf_path = 'entry/measurement/Pilatus/data'

    def initialize(self):
        self.proxy = PyTango.DeviceProxy(self.device_name)
        # set a long Tango timeout, as the Pilatus doesn't stop during frames.
        self.proxy.set_timeout_millis(60000)
        self.burst_latency = .003

    @property
    def energy(self):
        return self.proxy.energy

    @energy.setter
    def energy(self, val):
        self.proxy.energy = val

    def prepare(self, acqtime, dataid, n_starts):
        """
        Run before acquisition, once per scan. Set up triggering,
        number of images etc.
        """

        self.arm_number = -1

        if self.busy():
            raise Exception('%s is busy!' % self.name)

        if dataid is None:
            # no saving
            self.saving_file = ''
        else:
            # saving
            path = env.paths.directory
            fn = 'scan_%06d_%s.hdf5' % (dataid, self.name)
            self.saving_file = os.path.join(path, fn)
            if os.path.exists(self.saving_file):
                print('%s: this hdf5 file exists, I am raising an error now'%self.name)
                raise Exception('%s hdf5 file already exists' % self.name)

        self.proxy.exptime = acqtime
        self.proxy.expperiod = self.burst_latency + acqtime

    def arm(self):
        """
        Start the detector if hardware triggered, just prepareAcq otherwise.
        """
        if self.busy():
            raise Exception('%s is busy!' % self.name)
        self.arm_number += 1

        if self.hw_trig and (self.burst_n == 1):
            # each image triggered
            self.proxy.nimages = self.hw_trig_n
            self.proxy.extmtrigger(self.saving_file)
        elif self.hw_trig and (self.burst_n > 1):
            # triggered burst mode
            self.proxy.nimages = self.burst_n
            self.proxy.exttrigger(self.saving_file)

    def start(self):
        """
        Start acquisition when software triggered.
        """
        if self.hw_trig:
            return
        if self.busy():
            raise Exception('%s is busy!' % self.name)
        self.proxy.nimages = self.burst_n
        self.proxy.exposure(self.saving_file)

    def stop(self):
        try:
            self.proxy.stop()
            self.stop_live()
        except PyTango.DevFailed as e:
            print('\n', e.args[0].desc)

    def busy(self):
        return not (self.proxy.State() == PyTango.DevState.ON)

    def read(self):
        if self.saving_file == '':
            return None
        else:
            return {'frames': Link(self.saving_file , self._hdf_path, universal=True)}
