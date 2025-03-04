from contrast.scans.Scan import SoftwareScan
from contrast.motors import all_are_motors
from contrast.environment import macro, env, MacroSyntaxError, runCommand
from contrast.detectors import Detector, DetectorGroup, TriggeredDetector, TriggerSource
from contrast.recorders import active_recorders, RecorderHeader, RecorderFooter
import contrast.colors as colors
from collections import OrderedDict
import time


@macro
class TriggerBurst(SoftwareScan):
    """
    Hardware controlled equivalent of a loop scan. No motores moving. Just multiple exposures at the same point.
    But instead of software triggers, this macro creates a quick succession of hardware triggers.

    Usage:
        %triggerburst <N_triggers> <rate_Hz> <delay_ns> <fix_rate_bool>
    """

    panda = None

    def __init__(self, *args, **kwargs):
        """
        Parse arguments.
        """
        self.flyscan = True
        self.N_triggers = int(args[0])
        self.rate_Hz = float(args[1])
        self.delay_ns = float(args[2])
        self.fix_rate_bool = bool(args[3])
        self.print_progress = False
        super(TriggerBurst, self).__init__(float(1. / self.rate_Hz))

        if self.panda is None:
            raise Exception('Set TriggerBurst.panda to your panda master')
        print('TriggerBurst controlled by %s' % self.panda.name)
        
        ## find the longest trigger latency of all active triggered detectors
        #min_latency = 0
        #for d in Detector.get_active():
        #    if isinstance(d, TriggeredDetector):
        #        if d.hw_trig_min_latency > min_latency:
        #            min_latency = d.hw_trig_min_latency

        
        if self.fix_rate_bool:  
            # fixing the rate at which frames are taken / triggers are send
            # step time = 1/frequency
            self.trig_up_time = float(1. / self.rate_Hz / 2.)
            self.trig_step_time = float(1. / self.rate_Hz) 
            self.trig_delay_time = self.trig_step_time - self.trig_up_time
            self.exptime = float(1. / self.rate_Hz / 1.) - (self.delay_ns  * 1.e-9)
        else:
            # fixing the exposure time of a frame
            # step time = 1/frequency + delay
            self.trig_up_time = float(1. / self.rate_Hz / 2.)
            self.trig_step_time = float(1. / self.rate_Hz) + (self.delay_ns  * 1.e-9)
            self.trig_delay_time = self.trig_step_time - self.trig_up_time
            self.exptime = float(1. / self.rate_Hz / 1.)
        self._print_setting()

    def _generate_positions(self):
        # dummy positions with a non existent motor
        yield {'fake': 0}


    def _set_det_trig(self, on):
        # special treatment for the panda box which rules all
        panda = self.panda
        # set up all triggered detectors
        for d in Detector.get_active():
            if isinstance(d, TriggeredDetector) and not d.name == panda.name:
                d.hw_trig = True   # hw_trig is not set back to False after the scan
                d.hw_trig_n = self.N_triggers
        if on:
            self.old_hw_trig = panda.hw_trig
            self.old_burst_n = panda.burst_n
            self.old_burst_lat = panda.burst_latency
            panda.burst_n = self.N_triggers
            panda.burst_latency = self.delay_ns * 1.e-9
            self.panda.query('PULSE1.PULSES=%d' % self.N_triggers)
            self.panda.query(f'PULSE1.WIDTH={self.trig_up_time:.8f}')  
            self.panda.query(f'PULSE1.DELAY={self.trig_delay_time:.8f}')            
            self.panda.query(f'PULSE1.STEP={self.trig_step_time:.8f}')   
            panda.hw_trig_n = 1
            panda.hw_trig = on
        else:
            panda.burst_n = self.old_burst_n
            panda.burst_latency = self.old_burst_lat
            panda.hw_trig = self.old_hw_trig

    def _print_setting(self):
        print(f'    Will create {self.N_triggers} triggers.')
        print(f'    Triggers will come every {self.trig_step_time} seconds ({1/self.trig_step_time} Hz).')
        print(f'    Triggers will stay high for {self.trig_up_time} seconds.')
        print(f'    Detectors are set to explose for {self.exptime} seconds ({1/self.exptime} Hz).')

    def run(self):
        """
        try:
            # start by setting up triggering on all compatible detectors
            self._set_det_trig(True)

            # we'll also need the pandabox
            self.panda.active = True

            # run the main part
            #self.panda.query('%s.A=1' % self.panda.bitblock)
            #self.panda.query('%s.A=0' % self.panda.bitblock)
            #super(TriggerBurst, self).run()
        """
        #as
        """
        This is the main acquisition loop where interaction with motors,
        detectors and other ``Gadget`` objects happens.
        """
        self._before_scan()
        print(f'\nScan {colors.str_scannumber(self.scannr)} starting at {time.asctime()}\n')

        # find and prepare the detectors
        det_group = DetectorGroup(*[d for d in Detector.get_active() if d.name != self.panda.name]) 
        det_group_extended = Detector.get_active()
        trg_group = TriggerSource.get_active()
        group = det_group + trg_group
        if group.busy():
            print('These gadgets are busy: %s'
                  % (', '.join([d.name for d in group if d.busy()])))
            return
        # start by setting up triggering on all compatible detectors
        self._set_det_trig(True)
        group.prepare(self.exptime, self.scannr, self.N_triggers, trials=10)
        t0 = time.time()

        # send a header to the recorders
        snap = env.snapshot.capture()
        for r in active_recorders():
            r.queue.put(RecorderHeader(scannr=self.scannr,
                                       status='started',
                                       path=env.paths.directory,
                                       snapshot=snap,
                                       description=self._command))
        try:
            # we'll also need the pandabox
            self.panda.active = True
            self.panda.arm()
            group.arm()
            group.start(trials=10)


            time.sleep(2)

            # set panda trigger counter to 0
            self.counter_start = self._get_panda_trigger_count()

            # blink the first bit to start the trigger train
            self.panda.query('%s.A=1' % self.panda.bitblock)
            self.panda.query('%s.A=0' % self.panda.bitblock)

            while group.busy() or self.panda.busy():
                time.sleep(1)
                self._while_acquiring()

            # read detectors and motors
            dt = time.time() - t0
            dct = OrderedDict()
            for d in det_group_extended:
                dct[d.name] = d.read()
            dct['dt'] = dt
            # pass data to recorders
            for r in active_recorders():
                r.queue.put(dct)
            print(f'\nScan {colors.str_scannumber(self.scannr)} ending at {time.asctime()}')

            # tell the recorders that the scan is over
            for r in active_recorders():
                r.queue.put(RecorderFooter(scannr=self.scannr,
                                           status='finished',
                                           path=env.paths.directory,
                                           snapshot=snap,
                                           description=self._command))

        except KeyboardInterrupt:
            group.stop()
            print(f'\nScan {colors.str_scannumber(self.scannr)} cancelled at {time.asctime()}')
            # tell the recorders that the scan was interrupted
            for r in active_recorders():
                r.queue.put(RecorderFooter(scannr=self.scannr,
                                           status='interrupted',
                                           path=env.paths.directory,
                                           snapshot=snap,
                                           description=self._command))

        except:
            self._cleanup()
            raise

        self._cleanup()

    def _cleanup(self):
        # set back the triggering state
        self._set_det_trig(False)

    def _before_start(self):
        pass


    def _get_panda_trigger_count(self):
        return int(self.panda.query('COUNTER5.OUT?')[4:].replace('\n',''))

    def _while_acquiring(self):
        #pass
        counters = self._get_panda_trigger_count() - self.counter_start
        print(f'\rEstimated time left {(self.N_triggers-counters) * self.trig_step_time:.3f} s', end='')