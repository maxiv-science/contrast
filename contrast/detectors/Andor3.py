if __name__ == '__main__':
    from contrast.detectors.Detector import (
        Detector, SoftwareLiveDetector, TriggeredDetector, BurstDetector)
    from contrast.environment import env
    from contrast.recorders.Hdf5Recorder import Link
else:
    from .Detector import (
        Detector, SoftwareLiveDetector, TriggeredDetector, BurstDetector)
    from ..environment import env
    from ..recorders.Hdf5Recorder import Link
import os
import PyTango


class Andor3(Detector, SoftwareLiveDetector, BurstDetector):
    """
    Provides an interface to the Andor3 Zyla streaming manager,

    https://github.com/maxiv-science/andor-streamer

    Note: hw trigger not yet implemented.
    """

    def __init__(self, device='zyla/test/1', name=None):
        SoftwareLiveDetector.__init__(self)
        BurstDetector.__init__(self)
        # last so that initialize() can overwrite parent defaults:
        Detector.__init__(self, name=name)
        self.proxy = PyTango.DeviceProxy(device)

    def initialize(self):
        pass

    def prepare(self, acqtime, dataid, n_starts):
        if self.busy():
            raise Exception('%s is busy!' % self.name)

        # saving and paths
        if dataid is None:
            # no saving
            self.saving_file = ''
            self.proxy.Filename = ''
        else:
            # saving
            path = env.paths.directory
            fn = 'scan_%06d_%s.hdf5' % (dataid, self.name)
            self.saving_file = os.path.join(path, fn)
            if os.path.exists(self.saving_file):
                print('%s: this hdf5 file exists, I am raising an error now'
                      % self.name)
                raise Exception('%s hdf5 file already exists' % self.name)
            self.proxy.Filename = self.saving_file

        # arming and numbers of frames
        self.proxy.ExposureTime = acqtime
        if self.burst_n == 1:
            self.proxy.TriggerMode = 'Software'
            self.proxy.nTriggers = n_starts
            self.proxy.Arm()
        else:
            self.proxy.TriggerMode = 'Internal'
            self.proxy.nTriggers = self.burst_n
        self.frames_expected = 0

    def arm(self):
        pass

    def start(self):
        if self.burst_n == 1:
            self.proxy.SoftwareTrigger()
            self.frames_expected += 1
        else:
            self.proxy.Arm()
            self.frames_expected = self.burst_n

    def stop(self):
        self.proxy.Stop()

    def busy(self):
        st = self.proxy.State()
        if st in (PyTango.DevState.STANDBY, PyTango.DevState.ON):
            return False
        elif st == PyTango.DevState.RUNNING:
            if self.proxy.nFramesAcquired == self.frames_expected:
                return False
        return True

    def read(self):
        if self.saving_file == '':
            return None
        else:
            return Link(
                self.saving_file, 'entry/instrument/andor', universal=True)
