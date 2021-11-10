from .Detector import TriggerSource, BurstDetector
import PyTango

class StanfordTriggerSource(TriggerSource, BurstDetector):
    """
    Class representing the DG645 as a simple source for hardware
    triggers. All channels are fired with the requested high
    time.
    """
    def __init__(self, name=None, device_name=None):
        self.device_name = device_name
        TriggerSource.__init__(self, name=name)
        BurstDetector.__init__(self)

    def initialize(self):
        self.proxy = PyTango.DeviceProxy(self.device_name)
        self.burst_latency = .001

    def prepare(self, acqtime, *args, **kwargs):
        BurstDetector.prepare(self, acqtime, dataid, n_starts)
        acqtime = self.acqtime
        self.proxy.TriggerSource = 5
        if self.burst_n > 1:
            self.proxy.BurstMode = True
            self.proxy.BurstCount = self.burst_n
            self.proxy.BurstPeriod = acqtime + self.burst_latency
        else:
            self.proxy.BurstMode = False
        self.proxy.OutputABWidth = acqtime
        self.proxy.OutputCDWidth = acqtime
        self.proxy.OutputEFWidth = acqtime
        self.proxy.OutputGHWidth = acqtime
        self.proxy.ChannelADelay = 0.0
        self.proxy.ChannelCDelay = 0.0
        self.proxy.ChannelEDelay = 0.0
        self.proxy.ChannelGDelay = 0.0

    def start(self):
        self.proxy.TriggerSingle()

