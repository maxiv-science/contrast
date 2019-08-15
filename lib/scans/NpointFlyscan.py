from .AScan import AScan
from ..motors import all_are_motors
from ..environment import macro, MacroSyntaxError
from ..detectors import Detector, TriggeredDetector

@macro
class NpointFlyscan(AScan):
    """
    Flyscan macro for the Npoint LC400 setup.
        
    npointflyscan <fly-motor> <start> <stop> <intervals> <step-motor1> <start1> <stop1> <intervals1> ... <exp time> <latency>

    The argument fly-motor must be an instance of the LC400Motor class.
    """

    def __init__(self, *args):
        """
        Parse arguments.
        """
        try:
            assert all_are_motors([fastmotor, slowmotor])
            super(NpointFlyscan, self).__init__(slowmotor, args[4:])
            self.fastmotor = args[0]
            self.fastlimits = [float(i) for i in args[1:3]]
            self.fastintervals = int(args[3])
            self.exptime = float(args[-2])
            self.latency = float(args[-1])
        except:
            raise MacroSyntaxError

    def _set_det_trig(self, on):
        for d in Detector.get_active_detectors():
            if isinstance(d, TriggeredDetector):
                d.hw_trig = on
                d.hw_trig_n = self.fastintervals + 1

    def run(self):
        # start by setting up triggering on all compatible detectors
        self._set_det_trig(True)

        # configure the SC device - roughly like this
        axismap = {'sz': 1, 'sx': 2, 'sy': 3}
        fast_axis = axismap[self.fastmotor]
        self.scancontrol = PyTango.DeviceProxy("lc400scancontrol/test/1")
        ### note: these Tango attributes might have different names, check in Jive
        self.scancontrol.write_attribute("FlyScanMotorStartPosition", self.fastlimits[0])
        self.scancontrol.write_attribute("FlyScanMotorEndPosition", self.fastlimits[1])
        self.scancontrol.write_attribute("NumberOfIntervals", self.fastintervals)
        self.scancontrol.write_attribute("GateWidth", self.exptime)
        self.scancontrol.write_attribute("GateLatency", self.latency)
        self.scancontrol.write_attribute("FlyScanMotorAxis", self.fastmotor.axis)
        self.scancontrol.ConfigureLC4400Motion()
        self.scancontrol.ConfigureLC4400Recorder()
        self.scancontrol.ConfigureStanford()
        self.scancontrol.ConfigureNi6602() # a historical feature of the scancontrol device - will get refactored into the Ni6602 device

        # run the main part
        super(NpointFlyscan, self).run()

        # set back the triggering state
        self._set_det_trig(False)

    def _before_start(self):
        # we need to call Go() on the SC device at some point, maybe here.
        self.scancontrol.Go()

