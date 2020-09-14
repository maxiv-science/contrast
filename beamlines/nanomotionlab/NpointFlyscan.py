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
        
    npointflyscan <fly-motor> <start> <stop> <intervals> <step-motor1> <start1> <stop1> <intervals1> ... <exp time> <latency>

    The argument fly-motor must be an instance of the LC400Motor class.
    """

    def __init__(self, *args):
        """
        Parse arguments.
        """
        print("*** __init__")
        try:
            assert all_are_motors(args[:-2:4])
            super(NpointFlyscan, self).__init__(*args[4:-1])
            self.fastmotor = args[0]
            # convert to dial coordinates, as the LC400 operates in dial units
            self.fastmotorstart = ( float(args[1]) - self.fastmotor._offset ) / self.fastmotor._scaling
            self.fastmotorend = ( float(args[2]) - self.fastmotor._offset ) / self.fastmotor._scaling
            self.fastmotorintervals = int(args[3])
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
                d.hw_trig_n = self.fastmotorintervals + 1
                d.burst_latency = self.latency

    def run(self):
        try:
            # start by setting up triggering on all compatible detectors
            self._set_det_trig(True)

            # Activate the LC400 buffer
            #runCommand('activate npoint_buff')

            # create waveform from scan parameters
            self.wf = LC400Waveform(self.fastmotor.axis, 
                               self.fastmotorstart,
                               self.fastmotorend,
                               self.fastmotorintervals+1,
                               self.exptime,
                               self.latency,
                               0.5, # acceleration time TODO make this a configurable parameter, e.g via a keyword parameter
                               )
            # get JSON config string and send it to the LC400 via the motor.proxy 
            json = self.wf.json()
            self.fastmotor.proxy.load_waveform(json)

            # move fast motor to start position of line
            self.fastmotor.dial_position = self.wf.absolutstartposition
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
        # deactivate position buffer
        # runCommand('deactivate npoint_buff')

        # set back the triggering state
        self._set_det_trig(False)

    def _before_start(self):
        ok = False
        while not ok:
            try:
                while self.fastmotor.proxy.waveform_is_running:
                    time.sleep(0.05)
                self.fastmotor.proxy.start_waveform()
                ok = True
            except:
                print('***** start_waveform() failed, is the piexo having trouble settling? trying again...')
                import time
                time.sleep(.1)

    def _while_acquiring(self):
        s = ''
        for d in Detector.get_active():
            if d.name in ('xspress3', 'merlin'):
                s += ('%s: %u, ' % (d.name, d.lima.last_image_acquired))
        print(s + '\r', end='')

