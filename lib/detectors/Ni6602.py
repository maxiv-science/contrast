from .Detector import Detector, LiveDetector, TriggeredDetector
import PyTango
import time

PROP_MAP = {1: 'counter01', 2: 'counter02', 3: 'counter03'}
CHANNEL_MAP = {'counter1': 'CNT1', 'counter2': 'CNT2', 'counter3': 'CNT3'}

class Ni6602CounterCard(Detector, LiveDetector, TriggeredDetector):
    """
    Interface to the Ni6602 Tango device exposing counters.
    """
    def __init__(self, name=None, device=None):
        self.dev_name = device
        Detector.__init__(self, name=name)
        LiveDetector.__init__(self)
        TriggeredDetector.__init__(self)

    def initialize(self):
        self.dev = PyTango.DeviceProxy(self.dev_name)
        self.dev.init()
        
        # handle some unwanted options that otherwise can cause errors
        self.dev.write_attribute("nexusFileGeneration", 0)
        self.dev.write_attribute("CNT1MinPulseWidthEnable", 0)
        self.dev.write_attribute("CNT2MinPulseWidthEnable", 0)
        self.dev.write_attribute("CNT3MinPulseWidthEnable", 0)

    def _toggle_PW_mode(self, pw):
        """
        Switch between PW (pulse-width gated) and EVT (single count) mode.
        This is done through Tango properties so is a bit messy.

        pw = True means go to gated mode, 
        pw = False means go to single count.
        """
        if pw:
            oldstr, newstr = 'Mode:EVT', 'Mode:PW'
        else:
            oldstr, newstr = 'Mode:PW', 'Mode:EVT'
        for prop_name in PROP_MAP.values():
            channel_props = self.dev.get_property(prop_name)[prop_name]
            for i, val in enumerate(channel_props):
                if val == oldstr:
                    channel_props[i] = newstr
                    self.dev.put_property({prop_name: channel_props})
                    break
            time.sleep(.1)
            self.dev.init()

    def prepare(self, acqtime, dataid):
        """
        Run before acquisition, once per scan. Set up triggering,
        number of images etc.
        """

        if self.busy():
            raise Exception('%s is busy!' % self.name)

        if self.hw_trig:
            self._toggle_PW_mode(True)
            self.dev.acquisitionMode = 'BUFFERED'
            self.dev.totalNbPoint = self.hw_trig_n
            self.dev.bufferDepth = self.hw_trig_n
        else:
            self._toggle_PW_mode(False)
            self.dev.acquisitionMode = 'SCALAR'
        self.dev.integrationTime = acqtime

    def start_live(self, acqtime=1.0):
        """
        The NI card can do on-board live mode.
        """
        self.dev.continuous = True
        self.dev.integrationTime = acqtime
        self.dev.Start()

    def stop_live(self):
        """
        The NI card can do on-board live mode.
        """
        self.stop()
        self.dev.continuous = False

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
        if self.hw_trig:
            return
        if self.busy():
            raise Exception('%s is busy!' % self.name)
        self.dev.Start()

    def stop(self):
        self.dev.Stop()
        while not self.dev.State() == PyTango.DevState.STANDBY:
            time.sleep(.01)

    def busy(self):
        return not (self.dev.State() == PyTango.DevState.STANDBY)

    def read(self):
        res = {}
        for name, channel in CHANNEL_MAP.items():
            res[name] = self.dev.read_attribute(channel).value
        return res

