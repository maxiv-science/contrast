from .Detector import Detector, TriggeredDetector
import PyTango
import numpy as np

class AdLinkAnalogInput(Detector, TriggeredDetector):
    """
    Interface to the AdLink Tango device exposing one analog input.
    """
    def __init__(self, name=None, device=None):
        self.dev_name = device
        Detector.__init__(self, name=name)
        TriggeredDetector.__init__(self)

    def initialize(self):
        self.dev = PyTango.DeviceProxy(self.dev_name)
        self.dev.init()
        
        self.stop() # needs to be in standby to change anything

        self.dev.write_attribute("TriggerSources", "ExtD:+")
        self.dev.write_attribute("TriggerMode", 1)
        self.dev.write_attribute("NumOfDisplayableTriggers", -1)
        self.dev.write_attribute("ChannelSamplesPerTrigger", 100)

    def prepare(self, acqtime, dataid):
        """
        Run before acquisition, once per scan. Set up triggering,
        number of images etc.
        """

        if self.busy():
            raise Exception('%s is busy!' % self.name)

        if self.hw_trig:
            # fixed at 100 samples per trigger in the Adlink device:
            srate = int(np.ceil(100.0 / acqtime))
            self.dev.write_attribute('NumOfTriggers', self.hw_trig_n)
            self.dev.write_attribute('SampleRate', srate)
        else:
            print('Warning: the AdLinkAnalogInput detector only works with hardware triggering.')

    def arm(self):
        """
        Start the detector if hardware triggered
        """
        if self.busy():
            raise Exception('%s is busy!' % self.name)
        if self.hw_trig:
            self.dev.Start()

    def start(self):
        """
        Start acquisition when software triggered.
        """
        pass

    def stop(self):
        if not self.dev.State() == PyTango.DevState.STANDBY:
            # AdLink gets angry if you stop it in standby
            self.dev.Stop()

    def busy(self):
        return (self.dev.State() == PyTango.DevState.RUNNING)

    def read(self):
        if not self.hw_trig:
            return -1
        vals = self.dev.read_attribute("C00_MeanValues").value
        self.dev.Stop() # have to explicitly call stop after the read
        return np.array(vals)

