from contrast.scans.Mesh import Mesh
from contrast.motors import all_are_motors
from contrast.environment import macro, MacroSyntaxError, runCommand
from contrast.detectors import Detector, TriggeredDetector
from contrast.motors.LC400 import LC400Waveform
import time


@macro
class NpointFlyscan(Mesh):
    """
    Flyscan macro for the Npoint LC400 setup.

    npointflyscan <fly-motor> <start> <stop> <intervals>
                  <step-motor1> <start1> <stop1> <intervals1>
                  ...
                  <exp time>

    The argument fly-motor must be an instance of the LC400Motor class.

    Optional keyword arguments:
      latency: set the latency time between detector acquisitions (default longest latency of active detector(s))
      acctime: set the acceleration time of the piezo (default acctime=0.1)
    """

    panda = None

    def __init__(self, *args, **kwargs):
        """
        Parse arguments.
        """
        assert all_are_motors(args[:-2:4])
        super(NpointFlyscan, self).__init__(*args[4:])
        self.fastmotor = args[0]
        # convert to dial coordinates, as the LC400 operates in dial units
        self.fastmotorstart = ((float(args[1]) - self.fastmotor._offset)
                               / self.fastmotor._scaling)
        self.fastmotorend = ((float(args[2]) - self.fastmotor._offset)
                             / self.fastmotor._scaling)
        self.fastmotorintervals = int(args[3])
        self.exptime = float(args[-1])
        self.print_progress = False
        self.acctime = (kwargs['acctime'] if 'acctime' in kwargs.keys()
                        else 0.1)
        if self.panda is None:
            raise Exception('Set NpointFlyscan.panda to your panda master')
        print('Flyscan controlled by %s' % self.panda.name)
        
        # find the longest trigger latency of all active triggered detectors
        min_latency = 0
        for d in Detector.get_active():
            if isinstance(d, TriggeredDetector):
                if d.hw_trig_min_latency > min_latency:
                    min_latency = d.hw_trig_min_latency

        # use user specified latency if given as keyword, otherwise use min_latency
        if 'latency' in kwargs.keys():
            if kwargs['latency'] < min_latency:
                raise ValueError(f"The specified latency {kwargs['latency']:g} s is shorter than the required hardware latency {min_latency:g} s of the active detector(s). Detector(s) will miss triggers.")
            self.latency = kwargs['latency']
            print(f"Latency set to {self.latency:g} s by user.")
        else:
            self.latency = min_latency
            print(f"Latency set to {self.latency:g} s, based on active detectors.")


    def _set_det_trig(self, on):
        # special treatment for the panda box which rules all
        panda = self.panda
        # set up all triggered detectors
        for d in Detector.get_active():
            if isinstance(d, TriggeredDetector) and not d.name == panda.name:
                d.hw_trig = on
                d.hw_trig_n = self.fastmotorintervals + 1
        if on:
            self.old_hw_trig = panda.hw_trig
            self.old_burst_n = panda.burst_n
            self.old_burst_lat = panda.burst_latency
            panda.burst_n = self.fastmotorintervals + 1
            panda.burst_latency = self.latency
            panda.hw_trig_n = 1
            panda.hw_trig = on
        else:
            panda.burst_n = self.old_burst_n
            panda.burst_latency = self.old_burst_lat
            panda.hw_trig = self.old_hw_trig

    def run(self):
        try:
            # start by setting up triggering on all compatible detectors
            self._set_det_trig(True)

            # we'll also need the pandabox
            self.panda.active = True

            # create waveform from scan parameters
            wf = LC400Waveform(self.fastmotor.axis,
                               self.fastmotorstart,
                               self.fastmotorend,
                               self.fastmotorintervals + 1,
                               self.exptime,
                               self.latency,
                               self.acctime,
                               )
            # reset all the channels before proceeding (otherwise the
            # output trigger breaks)
            resets = wf.reset_json()
            for r in resets:
                self.fastmotor.proxy.load_waveform(r)
            # get the real JSON config string and send it to the LC400
            # via the motor.proxy
            json = wf.json()
            self.fastmotor.proxy.load_waveform(json)

            # move fast motor to start position of line
            self.fastmotor.dial_position = wf.absolutstartposition
            # wait for move to finish
            while self.fastmotor.busy():
                time.sleep(0.01)

            # run the main part
            super(NpointFlyscan, self).run()
        except:
            self._cleanup()
            raise

        self._cleanup()

    def _cleanup(self):
        # set back the triggering state
        self._set_det_trig(False)
        self.fastmotor.proxy.stop_waveform()

    def _before_start(self):
        ok = False
        n = 0
        while not ok:
            try:
                while self.fastmotor.proxy.waveform_is_running:
                    time.sleep(0.05)
                self.fastmotor.proxy.start_waveform()
                ok = True
            except:
                n += 1
                if n >= 10:
                    print('***** start_waveform() failed %u times, is the ' % n
                          + 'piexo having trouble settling? trying again...')
                time.sleep(.1)

