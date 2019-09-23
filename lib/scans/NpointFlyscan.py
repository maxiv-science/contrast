from .Mesh import Mesh
from ..motors import all_are_motors
from ..environment import macro, MacroSyntaxError
from ..detectors import Detector, TriggeredDetector

@macro
class NpointFlyscan(Mesh):
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
            assert all_are_motors(args[:-2:4])
            super(NpointFlyscan, self).__init__(*args[4:-1])
            self.fastmotor = args[0]
            self.fastlimits = [float(i) for i in args[1:3]]
            self.fastintervals = int(args[3])
            self.exptime = float(args[-2])
            self.latency = float(args[-1])
        except:
            #raise MacroSyntaxError
            raise

    def _set_det_trig(self, on):
        for d in Detector.get_active_detectors():
            if isinstance(d, TriggeredDetector):
                d.hw_trig = on
                d.hw_trig_n = self.fastintervals + 1

    def _set_det_active(self, dets, on):
        for d in dets:
            d.active = on
            verb = {True: 'Activated', False: 'Deactivated'}[on]
            print('%s the position buffer detector %s' % (verb, d.name))

    def run(self):
        # start by setting up triggering on all compatible detectors
        self._set_det_trig(True)

        # As a convenience, make sure any LC400Buffer detectors are active
        from ..detectors.LC400Buffer import LC400Buffer
        inactive_buffs = []
        for d in LC400Buffer.getinstances():
            if not d.active:
                inactive_buffs.append(d)
        self._set_det_active(inactive_buffs, True)

        # configure the SC device - roughly like this
        axismap = {'sz': 1, 'sx': 2, 'sy': 3}
        fast_axis = axismap[self.fastmotor.name]
        import PyTango
        self.scancontrol = PyTango.DeviceProxy("B303A/CTL/FLYSCAN-02")
        ### note: these Tango attributes might have different names, check in Jive
        self.scancontrol.write_attribute("FlyScanMotorStartPosition", self.fastlimits[0])
        self.scancontrol.write_attribute("FlyScanMotorEndPosition", self.fastlimits[1])
        self.scancontrol.write_attribute("NumberOfIntervals", self.fastintervals)
        self.scancontrol.write_attribute("GateWidth", self.exptime)
        self.scancontrol.write_attribute("GateLatency", self.latency)
        self.scancontrol.write_attribute("FlyScanMotorAxis", self.fastmotor.axis)
        self.scancontrol.ConfigureLC400Motion()
        self.scancontrol.ConfigureLC400Recorder()
        self.scancontrol.ConfigureStanford()

        # run the main part
        super(NpointFlyscan, self).run()

        # deactivate position buffer detectors that were not active before
        self._set_det_active(inactive_buffs, False)

        # set back the triggering state
        self._set_det_trig(False)

    def _before_start(self):
        # we need to call Go() on the SC device at some point, maybe here.
        self.scancontrol.Go()

    def _while_acquiring(self):
        s = ''
        for d in Detector.get_active_detectors():
            if d.name in ('xspress3', 'pilatus', 'pilatus1m', 'merlin'):
                s += ('%s: %u, ' % (d.name, d.lima.last_image_acquired))
        print(s + '\r', end='')

