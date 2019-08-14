from .AScan import AScan
from ..motors import all_are_motors
from ..environment import macro, MacroSyntaxError
from ..detectors import Detector, TriggeredDetector

@macro
class NpointFlyscan(AScan):
    """
    Flyscan macro for the Npoint LC400 setup.
        
    npointflyscan <fly-motor> <start> <stop> <intervals> <step-motor1> <start> <stop> <intervals> <exp time>

    The argument fly-motor must be an instance of the E727 motor class.
    """

    def __init__(self, *args):
        """
        Parse arguments.
        """
        try:
            assert (len(args) == 9)
            exposuretime = float(args[8])
            super(AScan, self).__init__(exposuretime)
            self.fastmotor = args[0]
            self.fastlimits = [float(m) for m in args[1:3]]
            self.fastintervals = int(args[3])
            self.slowmotor = args[4]
            self.slowlimits = [float(m) for m in args[5:7]]
            self.slowintervals = int(args[7])
            assert all_are_motors([self.fastmotor, self.slowmotor])
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
        self.scancontrol.write_attribute("FlyScanMotorStartPosition", int(self.start_pos_fly) )
        self.scancontrol.write_attribute("FlyScanMotorEndPosition", int(self.final_pos_fly) )
        self.scancontrol.write_attribute("NumberOfIntervals", nr_interv_fly )
        self.scancontrol.write_attribute("GateWidth", exposure_time )
        self.scancontrol.write_attribute("GateLatency", latency_time )
        self.scancontrol.write_attribute("FlyScanMotorAxis", fast_axis)

        # run the main part
        super(NpointFlyscan, self).run()

        # set back the triggering state
        self._set_det_trig(False)

    def _before_start(self):
        # we need to call Go() on the SC device at some point, maybe here.
        self.scancontrol.Go()
