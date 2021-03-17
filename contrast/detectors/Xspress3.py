from .Detector import Detector, SoftwareLiveDetector, TriggeredDetector, BurstDetector
from ..environment import env
from ..recorders.Hdf5Recorder import Link
import os
try:
    import PyTango
except ModuleNotFoundError:
    pass
import time

class Xspress3(Detector, SoftwareLiveDetector, TriggeredDetector, BurstDetector):
    """
    Provides an interface to the Xspress3 streaming manager,

    https://github.com/maxiv-science/xspress3-streamer
    """

    def __init__(self, device='staff/alebjo/xspress3', name=None):
        SoftwareLiveDetector.__init__(self)
        TriggeredDetector.__init__(self)
        BurstDetector.__init__(self)
        Detector.__init__(self, name=name) # last so that initialize() can overwrite parent defaults
        self.proxy = PyTango.DeviceProxy(device)

    def initialize(self):
        self.burst_latency = 100e-9

    def prepare(self, acqtime, dataid, n_starts):
        if self.busy():
            raise Exception('%s is busy!' % self.name)

        # saving and paths
        if dataid is None:
            # no saving
            self.saving_file = ''
            self.proxy.DestinationFileName = self.saving_file
        else:
            # saving
            path = env.paths.directory
            fn = 'scan_%06d_%s.hdf5' % (dataid, self.name)
            self.saving_file = os.path.join(path, fn)
            if os.path.exists(self.saving_file):
                print('%s: this hdf5 file exists, I am raising an error now'%self.name)
                raise Exception('%s hdf5 file already exists' % self.name)
            self.proxy.DestinationFileName = self.saving_file

        # arming and numbers of frames
        self.proxy.ExposureTime = acqtime
        self.proxy.nFramesPerTrigger = self.burst_n
        self.proxy.LatencyTime = self.burst_latency
        if self.hw_trig:
            self.proxy.TriggerMode = 'EXTERNAL'
        else:
            self.proxy.TriggerMode = 'SOFTWARE'

        # if not in burst mode, we can arm here and then just soft trigger
        ntrig = 1
        self.arm_calls = 0
        if self.burst_n == 1:            
            ntrig *= n_starts
        if self.hw_trig:
            ntrig *= self.hw_trig_n
        self.proxy.nTriggers = ntrig
        if self.burst_n == 1:
            self.proxy.Arm()

        # so how many frames do we expect to see before the detector is done with a specific start()?
        exp = self.burst_n
        if self.hw_trig:
            exp *= self.hw_trig_n
        self.expected_per_arm = exp
        self.expected_total = 0

    def arm(self):
        # in burst mode, we have to arm here, otherwise it's already done
        if self.burst_n > 1:
            self.proxy.Arm()
            self.expected_total = self.expected_per_arm
        else:
            self.expected_total += self.expected_per_arm

    def start(self):
        if self.hw_trig:
            return
        self.proxy.SoftwareTrigger()

    def stop(self):
        self.proxy.Stop()

    def busy(self):
        while True:
            try:
                st = self.proxy.State()
                if st == PyTango.DevState.STANDBY:
                    return False
                elif st == PyTango.DevState.RUNNING:
                    if self.proxy.nFramesAcquired == self.expected_total:
                        return False
                return True
            except PyTango.DevFailed:
                print('%s.busy(): failed to talk to my Tango device, trying again...'%self.name)
                time.sleep(.5)

    def read(self):
        if self.saving_file == '':
            return None
        else:
            return Link(self.saving_file , '/', universal=True)

