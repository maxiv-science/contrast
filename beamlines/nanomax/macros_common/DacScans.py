from contrast.motors import all_are_motors
from contrast.environment import macro, env, MacroSyntaxError, runCommand
from contrast.detectors import Detector, TriggeredDetector, TriggerSource
from contrast.recorders import active_recorders, RecorderHeader, RecorderFooter
from contrast.utils import SpecTable
from collections import OrderedDict
import sys

import time
import sys
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

@macro
class Cspiral():
    """
    Continuous spiral scan macro for the NI dac box.

    csnake <step size> <positions> <exp time>

    """

    panda = None
    dac_0 = None
    dac_1 = None

    def __init__(self, *args, **kwargs):
        """
        Parse arguments
        """
        self._command = None  # updated if run via macro
        self.scannr = env.nextScanID
        self.print_progress = True
        env.nextScanID += 1
        self.stepsize = float(args[0])
        self.n_steps = int(args[1])
        self.exptime = float(args[2])
        self.latency = 0.001
        self.print_progress = False
        if self.panda is None:
            raise Exception('Set DacScan.panda to your panda master')
        #print('Flyscan controlled by %s' % self.panda.name)

    def _set_det_trig(self, on):
        # special treatment for the panda box which rules all
        panda = self.panda
        panda.stop()
        # set up all triggered detectors
        for d in Detector.get_active():
            if isinstance(d, TriggeredDetector) and not d.name == panda.name:
                d.hw_trig = on
                d.hw_trig_n = self.n_steps
        if on:
            self.old_hw_trig = panda.hw_trig
            self.old_burst_n = panda.burst_n
            self.old_burst_lat = panda.burst_latency
           # print(f"{self.n_steps = }")
            panda.burst_n = self.n_steps
            panda.burst_latency = self.latency
            panda.hw_trig_n = 1
            panda.hw_trig = on
        else:
            panda.burst_n = self.old_burst_n
            panda.burst_latency = self.old_burst_lat
            panda.hw_trig = self.old_hw_trig

    def _while_acquiring(self):
        x = self.dac_0.position()
        y = self.dac_1.position()
        et = self.dac_0.proxy.get_end_time()
        print('\rEstimated finish time: %s - X:%7.3f um Y:%7.3f um' % (et, x, y), end='') 

    def run(self):
        """
        This is the main acquisition loop where interaction with motors,
        detectors and other ``Gadget`` objects happens.
        """
        print('\nScan #%d starting at %s\n' % (self.scannr, time.asctime()))

        # find and prepare the detectors
        det_group = Detector.get_active()
        trg_group = TriggerSource.get_active()
        group = det_group + trg_group
        if group.busy():
            print('These gadgets are busy: %s'
                  % (', '.join([d.name for d in group if d.busy()])))
            return
        # start by setting up triggering on all compatible detectors
        self._set_det_trig(True)
        group.prepare(self.exptime, self.scannr, self.n_steps,
                      trials=10)
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
            group.arm()
            group.start(trials=10)
            self.dac_0.proxy.spiral_scan([self.stepsize, self.n_steps, self.exptime+self.latency])
            while det_group.busy():
                time.sleep(1)
                self._while_acquiring()
            # read detectors and motors
            dt = time.time() - t0
            dct = OrderedDict()
            for d in det_group:
                dct[d.name] = d.read()
            dct['dt'] = dt
            # pass data to recorders
            for r in active_recorders():
                r.queue.put(dct)
            print('\n\nScan #%d ending at %s' % (self.scannr, time.asctime()))

            # tell the recorders that the scan is over
            for r in active_recorders():
                r.queue.put(RecorderFooter(scannr=self.scannr,
                                           status='finished',
                                           path=env.paths.directory,
                                           snapshot=snap,
                                           description=self._command))

        except KeyboardInterrupt:
            group.stop()

            print('\nScan #%d cancelled at %s' % (self.scannr, time.asctime()))

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
        self.dac_0.proxy.stop_waveform()


@macro
class Csnake():
    """
    Continuous snake scan macro for the NI dac box.


    csnake <horizontal left> <horizontal right>
                    <vertical bottom> <vertical top>
                    <step size> <exp time>

    """

    panda = None
    dac_0 = None
    dac_1 = None

    def __init__(self, *args, **kwargs):
        """
        Parse arguments
        """
        self._command = None  # updated if run via macro
        self.scannr = env.nextScanID
        self.print_progress = True
        env.nextScanID += 1
       # convert to dial coordinates, as the dac operates in dial units
        self.dac_0_start = ((float(args[0]) - self.dac_0._offset)
                               / self.dac_0._scaling)
        self.dac_0_end = ((float(args[1]) - self.dac_0._offset)
                             / self.dac_0._scaling)
        self.dac_1_start = ((float(args[2]) - self.dac_1._offset)
                               / self.dac_1._scaling)
        self.dac_1_end = ((float(args[3]) - self.dac_1._offset)
                             / self.dac_1._scaling)
        self.stepsize = float(args[4])
        self.exptime = float(args[5])
        self.latency = 0.001
        self.n_steps = int(((self.dac_0_end - self.dac_0_start)/self.stepsize+1) * ((self.dac_1_end - self.dac_1_start)/self.stepsize+1)-1)
        self.print_progress = False
        if self.panda is None:
            raise Exception('Set DacScan.panda to your panda master')
        #print('Flyscan controlled by %s' % self.panda.name)

    def _set_det_trig(self, on):
        # special treatment for the panda box which rules all
        panda = self.panda
        panda.stop()
        # set up all triggered detectors
        for d in Detector.get_active():
            if isinstance(d, TriggeredDetector) and not d.name == panda.name:
                d.hw_trig = on
                d.hw_trig_n = self.n_steps
        if on:
            self.old_hw_trig = panda.hw_trig
            self.old_burst_n = panda.burst_n
            self.old_burst_lat = panda.burst_latency
           # print(f"{self.n_steps = }")
            panda.burst_n = self.n_steps
            panda.burst_latency = self.latency
            panda.hw_trig_n = 1
            panda.hw_trig = on
        else:
            panda.burst_n = self.old_burst_n
            panda.burst_latency = self.old_burst_lat
            panda.hw_trig = self.old_hw_trig

    def _while_acquiring(self):
        x = self.dac_0.position()
        y = self.dac_1.position()
        et = self.dac_0.proxy.get_end_time()
        print('\rEstimated finish time: %s - X:%7.3f um Y:%7.3f um' % (et, x, y), end='') 

    def run(self):
        """
        This is the main acquisition loop where interaction with motors,
        detectors and other ``Gadget`` objects happens.
        """
        print('\nScan #%d starting at %s\n' % (self.scannr, time.asctime()))

        # find and prepare the detectors
        det_group = Detector.get_active()
        trg_group = TriggerSource.get_active()
        group = det_group + trg_group
        if group.busy():
            print('These gadgets are busy: %s'
                  % (', '.join([d.name for d in group if d.busy()])))
            return
        # start by setting up triggering on all compatible detectors
        self._set_det_trig(True)
        group.prepare(self.exptime, self.scannr, self.n_steps,
                      trials=10)
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
            group.arm()
            group.start(trials=10)
            self.dac_0.proxy.snake_scan([self.dac_0_start, self.dac_0_end, self.dac_1_start, self.dac_1_end, self.stepsize, self.exptime+self.latency])
            while det_group.busy():
                time.sleep(1)
                self._while_acquiring()
            # read detectors and motors
            dt = time.time() - t0
            dct = OrderedDict()
            for d in det_group:
                dct[d.name] = d.read()
            dct['dt'] = dt
            # pass data to recorders
            for r in active_recorders():
                r.queue.put(dct)
            print('\n\nScan #%d ending at %s' % (self.scannr, time.asctime()))

            # tell the recorders that the scan is over
            for r in active_recorders():
                r.queue.put(RecorderFooter(scannr=self.scannr,
                                           status='finished',
                                           path=env.paths.directory,
                                           snapshot=snap,
                                           description=self._command))

        except KeyboardInterrupt:
            group.stop()

            print('\nScan #%d cancelled at %s' % (self.scannr, time.asctime()))

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
        self.dac_0.proxy.stop_waveform()

class dac_waveform():

    dac_rate  = 1000
    
    @classmethod
    def get_spiral_waveform(cls, stepsize, steps, exptime):
        nsamples = np.arange(0, cls.dac_rate * steps * exptime)
        A = stepsize * np.sqrt(nsamples/(cls.dac_rate*exptime*np.pi))
        B = np.sqrt(4 * np.pi * nsamples/(cls.dac_rate*exptime))
        spiral = np.append(A*np.cos(B), A*np.sin(B))
        wf = spiral.reshape((2, len(nsamples)))
        return wf

    @classmethod
    def get_snake_waveform(cls, x1, x2, y1, y2, stepsize, exptime):
        step = stepsize/(exptime*cls.dac_rate)
        nlines = int(round((y2-y1)/stepsize + 1, 0))
        wf = np.zeros((2, 0))
        for i in range(0, nlines):
            if i % 2:
                hx_segment = np.arange(x2, x1, -step)
                hy_segment = np.full((1,len(hx_segment)), i*stepsize + y1)
                vy_segment = np.arange(y1, y1+stepsize, step)
                vx_segment = np.full((1,len(vy_segment)), x1)
                h_segment = np.vstack([hx_segment, hy_segment])
                v_segment = np.vstack([vx_segment, vy_segment + i*stepsize])
            else:
                hx_segment = np.arange(x1, x2, step)
                hy_segment = np.full((1,len(hx_segment)), i*stepsize + y1)
                vy_segment = np.arange(y1, y1+stepsize, step)
                vx_segment = np.full((1,len(vy_segment)), x2)
                h_segment = np.vstack([hx_segment, hy_segment])
                v_segment = np.vstack([vx_segment, vy_segment + i*stepsize])
            wf = np.append(wf, h_segment, axis=1)        
            if i < nlines - 1:
                wf = np.append(wf, v_segment, axis=1)       
        last_point = np.array((x2, y2), ndmin=2).T
        wf = np.append(wf, last_point, axis=1)       
        return wf



