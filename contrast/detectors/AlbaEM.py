from .Detector import Detector, LiveDetector, TriggeredDetector, BurstDetector
try:
    import PyTango
except ModuleNotFoundError:
    pass
import time

class AlbaEM(Detector, LiveDetector, TriggeredDetector, BurstDetector):
    """
    Interface to the Alba electrometer Tango device,

    https://gitlab.maxiv.lu.se/alebjo/dev-nanomax-albaem
    """
    def __init__(self, name=None, device=None):
        self.dev_name = device
        Detector.__init__(self, name=name)
        LiveDetector.__init__(self)
        TriggeredDetector.__init__(self)
        BurstDetector.__init__(self)

    def initialize(self):
        self.dev = PyTango.DeviceProxy(self.dev_name)
        self.dev.init()
        self.burst_latency = 320e-6

    def prepare(self, acqtime, dataid, n_starts):
        """
        Run before acquisition, once per scan. Set up triggering,
        number of images etc.
        """
        self.acqtime = acqtime
        if self.busy():
            raise Exception('%s is busy!' % self.name)

    def start_live(self, acqtime=1.0):
        """
        The Alba EM:s are always in live mode, exposing the
        "instant current" values.
        """
        pass

    def stop_live(self):
        """
        Nothing to do...
        """
        pass

    def arm(self):
        """
        Start the detector if hardware triggered
        """
        if self.busy():
            raise Exception('%s is busy!' % self.name)
        if self.hw_trig:
            self.dev.hw_measure((self.acqtime, self.hw_trig_n, 1)) # trigger on DIO_1

    def start(self):
        """
        Start acquisition when software triggered.
        """
        if self.hw_trig:
            return
        if self.busy():
            raise Exception('%s is busy!' % self.name)
        self.dev.sw_measure((self.acqtime, self.burst_n, self.burst_latency))

    def stop(self):
        self.dev.stop()
        while not self.dev.State() == PyTango.DevState.ON:
            time.sleep(.01)

    def busy(self):
        return not (self.dev.State() == PyTango.DevState.ON)

    def read(self):
        res = {}
        self.dev.read()
        for ch in (1,2,3,4):
            a = self.dev.read_attribute('data_%u'%ch).value
            res[ch] = a[0] if len(a)==1 else a
        return res

