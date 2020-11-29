from contrast.scans.Mesh import Mesh
from contrast.motors import all_are_motors
from contrast.environment import macro, MacroSyntaxError, runCommand
from contrast.detectors import Detector, TriggeredDetector
from contrast.motors.LC400 import LC400SteppedWaveform
import time

@macro
class NpointStepscan(Mesh):
    """
    Continuous step scan macro for the Npoint LC400 setup.
        
    npointstepscan <fast-motor> <start> <stop> <intervals> <step-motor1> <start1> <stop1> <intervals1> ... <exp time> <latency> 

    The argument fast-motor must be an instance of the LC400Motor class.

    Optional keyword arguments:
      jitter : randomizes perfect grid positions (default=0.0)
    """

    def __init__(self, *args, **kwargs):
        """
        Parse arguments.
        """
        try:
            assert all_are_motors(args[:-2:4])
            super(NpointStepscan, self).__init__(*args[4:-1], **kwargs)
            self.fastmotor = args[0]
            # convert to dial coordinates, as the LC400 operates in dial units
            self.fastmotorstart = ( float(args[1]) - self.fastmotor._offset ) / self.fastmotor._scaling
            self.fastmotorend = ( float(args[2]) - self.fastmotor._offset ) / self.fastmotor._scaling
            self.fastmotorintervals = int(args[3])
            self.exptime = float(args[-2])
            self.latency = float(args[-1])
            self.print_progress = False
            self.jitter = kwargs['jitter'] if 'jitter' in kwargs.keys() else 0.0
            self.panda = [d for d in Detector.get_active() if d.name=='panda0'][0]
        except:
            #raise MacroSyntaxError
            raise

    def _set_det_trig(self, on):
        # set up all triggered detectors
        for d in Detector.get_active():
            if isinstance(d, TriggeredDetector) and not d.name=='panda0':
                d.hw_trig = on
                d.hw_trig_n = self.fastmotorintervals + 1
        # special treatment for the panda0 which rules all
        panda = self.panda
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
            
            self.wf = LC400SteppedWaveform(self.fastmotor.axis,
                                self.fastmotorstart,
                                self.fastmotorend,
                                self.fastmotorintervals+1,
                                self.exptime,
                                self.latency,
                                self.jitter,
                                )
            # configure the internal recorder
            # TODO configure only if npointbuffer detector is active
            # self.fastmotor.proxy.configure_recording(self.wf.configure_recorder_json())
            
            # move fast motor to start position of line
            self.fastmotor.dial_position = self.wf.absolutstartposition
            # wait for move to finish
            while self.fastmotor.busy():
                time.sleep(0.01)

            # run the main part
            super(NpointStepscan, self).run()
        except:
            self._cleanup()
            raise
        # wait for waveform and recorder to finish
        while self.fastmotor.proxy.waveform_is_running or self.fastmotor.proxy.is_recording:
                    time.sleep(0.05)
                    print(".",end='')
        self._cleanup()

    def _cleanup(self):
        # set back the triggering state
        self._set_det_trig(False)
        self.fastmotor.proxy.stop_waveform()
        # TODO stop only if npointbuffer detector is active
        # print("stop recording")
        # self.fastmotor.proxy.stop_recording()

    def _before_start(self):
        # in burst mode, acquisition times are interpreted as acquisition
        # periods. in this case, since the panda box is in burst mode bur
        # the other detector probably aren't, we should add the latency
        # to the pandabox.
        self.panda.prepare(self.exptime+self.latency, self.scannr, self.n_positions)
        ok = False
        n = 0
        while not ok:
            try:
                while self.fastmotor.proxy.waveform_is_running:
                    time.sleep(0.05)
                ok = True
            except:
                n += 1
                if n >= 10:
                    print('***** start_waveform() failed %u times, is the piexo having trouble settling? trying again...'%n)
                time.sleep(.1)
        
        print("create and load wf in scan macro")
        # get the real JSON config string and send it to the LC400 via the motor.proxy
        json = self.wf.json()
        # move fast motor to start position of line
        #self.fastmotor.dial_position = self.wf.absolutstartposition
        #time.sleep(self.latency)
        self.fastmotor.proxy.load_waveform(json)
        # TODO start recorder only if npointbuffer detector is active
        # self.fastmotor.proxy.start_recording()
        # start the execution of the waveform
        self.fastmotor.proxy.start_waveform()

    def _while_acquiring(self):
        s = ''
        s += ('%s: %.3f, ' % (self.fastmotor.name, self.fastmotor.position()*self.fastmotor._scaling))
        for d in Detector.get_active():
            if d.name in ('xspress3',):
                s += ('%s: %u, ' % (d.name, d.lima.last_image_acquired))
        print(s + '\r', end='')

