from contrast.scans.Mesh import Mesh
from contrast.motors import all_are_motors
from contrast.environment import macro, MacroSyntaxError, runCommand
from contrast.detectors import Detector, TriggeredDetector

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
            self.print_progress = False
        except:
            #raise MacroSyntaxError
            raise

    def _set_det_trig(self, on):
        for d in Detector.get_active():
            if isinstance(d, TriggeredDetector):
                d.hw_trig = on
                d.hw_trig_n = self.fastintervals + 1

    def run(self):
        try:
            # start by setting up triggering on all compatible detectors
            self._set_det_trig(True)

            # Activate the LC400 buffer and deactivate the stanford box
            runCommand('deactivate stanford')
            runCommand('activate npoint_buff')
            runCommand('lima_hybrid_off')

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
        except:
            self._cleanup()
            raise

        self._cleanup()

    def _cleanup(self):
        # deactivate position buffer
        runCommand('deactivate npoint_buff')

        # set back the triggering state
        self._set_det_trig(False)

    def _before_start(self):
        # we need to call Go() on the SC device at some point, maybe here.
        ok = False
        while not ok:
            try:
                self.scancontrol.Go()
                ok = True
            except:
                print('***** scancontrol Go() failed, is the piezo having trouble settling? trying again...')
                import time
                time.sleep(.1)

    def _while_acquiring(self):
        s = ''
        for d in Detector.get_active():
            if d.name in ('xspress3', 'merlin'):
                s += ('%s: %u, ' % (d.name, d.lima.last_image_acquired))
        print(s + '\r', end='')

