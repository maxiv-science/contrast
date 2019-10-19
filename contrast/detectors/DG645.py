from . import TriggerSource
import PyTango

class StanfordTriggerSource(TriggerSource):
    """
    Class representing the DG645 as a simple source for hardware
    triggers. All channels are fired with the requested high
    time.
    """
    def __init__(self, name=None, device_name=None):
        self.device_name = device_name
        super(StanfordTriggerSource, self).__init__(name=name)

    def initialize(self):
        self.proxy = PyTango.DeviceProxy(self.device_name)

    def prepare(self, acqtime, *args, **kwargs):
        self.proxy.TriggerSource = 5
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

