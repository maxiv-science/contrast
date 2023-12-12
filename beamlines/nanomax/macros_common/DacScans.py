from contrast.motors import all_are_motors
from contrast.environment import macro, env, MacroSyntaxError, runCommand
from contrast.detectors import Detector, TriggeredDetector, TriggerSource
from contrast.recorders import active_recorders, RecorderHeader, RecorderFooter
from contrast.utils import SpecTable
from contrast.scans.Scan import SoftwareScan
from collections import OrderedDict
import sys

import time
import sys
import h5py
import os
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

class dac_waveform():

    dac_rate  = 1000
    ttl_high = 16.5 # this equals a high ttl pulse output. 3.3 volt

    @classmethod
    def save_h5_file(cls, path, waveform):
        wf_file = path
        #wf_file = os.path.join(path)
        with h5py.File(wf_file, 'w') as ofp:
            ofp.create_dataset('entry/measurement/waveform/data', data=waveform, compression='gzip')

    # -------------------------- Old waveform methods -------------------------
    @classmethod
    def get_spiral_waveform(cls, stepsize, steps, exptime):
        nsamples = np.arange(0, cls.dac_rate * steps * exptime)
        A = stepsize * np.sqrt(nsamples/(cls.dac_rate*exptime*np.pi))
        B = np.sqrt(4 * np.pi * nsamples/(cls.dac_rate*exptime))
        spiral = np.append(A*np.cos(B), A*np.sin(B))
        spiral = np.append(spiral, np.zeros(2*len(nsamples)))
        wf = spiral.reshape((4, len(nsamples)))
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
        wf = np.append(wf, np.zeros(wf.shape), axis=0)
        return wf

    # -------------------------- new waveform methods -------------------------
    @classmethod
    def get_spiral_wf(cls, stepsize, steps, latency, exptime, step_scan):
        pixeltime = (latency + exptime)
        spiral = None
        if step_scan:
            #step scanning
            npositions = np.arange(0, steps)
            A = stepsize * np.sqrt(npositions/np.pi)
            B = np.sqrt(4 * np.pi * npositions)
            spiral = np.append(A*np.cos(B), A*np.sin(B))
            spiral = np.repeat(spiral, cls.dac_rate*pixeltime)
        else:
            # continuous scanning
            npositions = np.arange(0, int(cls.dac_rate * steps * pixeltime))
            A = stepsize * np.sqrt(npositions/(cls.dac_rate*pixeltime*np.pi))
            B = np.sqrt(4 * np.pi * npositions/(cls.dac_rate*pixeltime))
            spiral = np.append(A*np.cos(B), A*np.sin(B))
        # adding zeros for the third channel
        spiral = np.append(spiral, np.zeros(int(cls.dac_rate * steps * pixeltime)))
        # adding the trigger pulse train on the furth channel
        pulse = np.zeros(int(latency*cls.dac_rate))
        pulse = np.append(pulse, np.full(int(exptime*cls.dac_rate), cls.ttl_high))
        pulses = np.tile(pulse,steps)
        pulses[-1] = 0
        spiral = np.append(spiral, pulses)
        wf = spiral.reshape((4, -1))
        return wf, steps

    @classmethod
    def get_snake_wf(cls, x1, x2, steps_x, y1, y2, steps_y, latency, exptime, step_scan):
        pixeltime = int(cls.dac_rate*(latency + exptime))
        nsteps = (steps_x+1) * (steps_y+1)-1
        stepsize_x = (x2-x1)/steps_x
        stepsize_y = (y2-y1)/steps_y

        if step_scan:
            # step scanning
            sec_x0 = np.linspace(x1, x2, steps_x+1)
            sec_x0 =np.repeat(sec_x0, pixeltime)
            sec_x2 = np.linspace(x2, x1, steps_x+1)
            sec_x2 =np.repeat(sec_x2, pixeltime)
            sec_y0 = np.full(pixeltime * (steps_x+1), y1)
            wf_x = sec_x0
            wf_y = sec_y0
            for i in range(1, steps_y+1):
                wf_y = np.append(wf_y, sec_y0+i*stepsize_y)
                if not i % 2:
                    wf_x = np.append(wf_x, sec_x0)
                else:
                    wf_x = np.append(wf_x, sec_x2)
        else:
            # contiuous scanning
            sec_x0 = np.linspace(x1, x2, pixeltime * steps_x)
            sec_x1 = np.full(pixeltime, x2)
            sec_x2 = np.linspace(x2, x1, pixeltime * steps_x)
            sec_x3 = np.full(pixeltime, x1)
            sec_y0 = np.full(pixeltime * steps_x, y1)
            sec_y1 = np.linspace(y1, y1+stepsize_y, pixeltime)
            sec_y1 = np.append(sec_y1, np.full(pixeltime * steps_x, y1+stepsize_y))
            wf_x = sec_x0
            wf_y = sec_y0
            for i in range(0, steps_y):
                if not i % 2:
                    wf_x = np.append(wf_x, sec_x1)
                    wf_x = np.append(wf_x, sec_x2)
                    wf_y = np.append(wf_y, sec_y1+i*stepsize_y)
                else:
                    wf_x = np.append(wf_x, sec_x3)
                    wf_x = np.append(wf_x, sec_x0)
                    wf_y = np.append(wf_y, sec_y1+i*stepsize_y)

        pulse = np.zeros(int(latency*cls.dac_rate))
        pulse = np.append(pulse, np.full(int(exptime*cls.dac_rate), cls.ttl_high))
        nsteps = int(wf_x.shape[0] / pixeltime)
        pulses = np.tile(pulse,nsteps)
        pulses[-1] = 0
        wf = np.vstack([wf_x, wf_y, np.zeros(len(pulses)),pulses])
        return wf, nsteps



class WFstepscan(SoftwareScan):
    """
    Base class for any step scan performed as a single waveform for the NI dac box.
    On purpuse this one is not a macro, so it can not be called by itself 
    """
    panda = None
    dac_0 = None
    dac_1 = None
    p_latency = 0.0001 

    def __init__(self, *args, **kwargs):
        # to be implemented by the exact shape of scan to be performed
        pass

    def _generate_waveform(self):
        # to be implemented by the exact shape of scan to be performed
        # return the waveform and the number of points in the scan
        pass

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
            panda.burst_n = 1
            panda.burst_latency = self.p_latency
            panda.hw_trig_n = self.n_steps
            panda.hw_trig = on
            # forcing the PandaBox to directly forward the given input TTL signal
            # and circumventing the internal pulse generator
            panda.query('%s.D=1' % panda.bitblock)
        else:
            panda.burst_n = self.old_burst_n
            panda.burst_latency = self.old_burst_lat
            panda.hw_trig = self.old_hw_trig
            panda.query('%s.D=0' % panda.bitblock)

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
        self._before_scan()
        print('\nScan #%d starting at %s\n' % (self.scannr, time.asctime()))

        # generating the waveform file
        print('Generating waveform file...   ', end='', flush=True)
        wf, self.n_steps = self._generate_waveform()
        wf_file=os.path.join(env.paths.directory, 'scan_%06u_waveform.hdf5'%self.scannr)
        dac_waveform.save_h5_file(wf_file, wf)
        self.dac_0.proxy.waveform_path = wf_file
        print('Waveform file generated ')

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
        group.prepare(self.exptime, self.scannr, 1,
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
            self.dac_0.proxy.start_waveform()
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

        # do any user-defined cleanup actions
        self._after_scan()



@macro
class WFspiral(WFstepscan):
    """
    Waveform spiral step scan

    wfspiral <step size> <positions> <exp time> <latency time>
    """

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
        self.latency = float(args[3])
        self.print_progress = False
        if self.panda is None:
            raise Exception('Set DacScan.panda to your panda master')

    def _generate_waveform(self):
        """
        create the wave form in shape of the step scanned spiral
        returns the waveform and the number of points in the scan
        """
        return dac_waveform.get_spiral_wf(self.stepsize, self.n_steps, self.latency, self.exptime, True)


@macro
class WFsnake(WFstepscan):
    """
    Waveform snake step scan

    wfsnake <horizontal left> <horizontal right> <steps>
            <vertical bottom> <vertical top> <steps>
            <exp time> <latency time> 
    """

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
        self.dac_1_start = ((float(args[3]) - self.dac_1._offset)
                               / self.dac_1._scaling)
        self.dac_1_end = ((float(args[4]) - self.dac_1._offset)
                             / self.dac_1._scaling)
        self.steps_x = int(args[2])
        self.steps_y = int(args[5])
        self.exptime = float(args[6])
        self.latency = float(args[7])
        self.print_progress = False
        if self.panda is None:
            raise Exception('Set DacScan.panda to your panda master')

    def _generate_waveform(self):
        """
        create the wave form in shape of the step scanned snake
        returns the waveform and the number of points in the scan
        """
        return dac_waveform.get_snake_wf(self.dac_0_start, self.dac_0_end, self.steps_x, 
                                         self.dac_1_start, self.dac_1_end, self.steps_y,
                                         self.latency, self.exptime, True)










class Cscan(SoftwareScan):
    """
    Base class for any continous(fly) performed as a single waveform for the NI dac box.
    On purpuse this one is not a macro, so it can not be called by itself 
    """

    panda = None
    dac_0 = None
    dac_1 = None

    def __init__(self, *args, **kwargs):
        # to be implemented by the exact shape of scan to be performed
        pass

    def _generate_waveform(self):
        # to be implemented by the exact shape of scan to be performed
        # only return waveform
        pass


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
            panda.burst_n = self.n_steps
            panda.burst_latency = self.latency
            panda.hw_trig_n = 1
            panda.hw_trig = on
            # setting the PandaBox up to create the actually used triggers
            # using its pulse generator timed to react on the first 
            # (and only) external trigger  
            panda.query('%s.D=0' % panda.bitblock)
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
        self._before_scan()
        print('\nScan #%d starting at %s\n' % (self.scannr, time.asctime()))

        # generating the waveform file
        print('Generating waveform file...   ', end='')
        wf = self._generate_waveform()
        wf_file=os.path.join(env.paths.directory, 'scan_%06u_waveform.hdf5'%self.scannr)
        dac_waveform.save_h5_file(wf_file, wf)
        self.dac_0.proxy.waveform_path = wf_file
        print('Waveform file generated ')

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
        group.prepare(self.exptime, self.scannr, 1,
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
            self.dac_0.proxy.start_waveform()
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

        # do any user-defined cleanup actions
        self._after_scan()



@macro
class Cspiral(Cscan):
    """
    Continuous spiral scan macro for the NI dac box.

    cspiral <step size> <positions> <exp time>
    """
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

    def _generate_waveform(self):
        # to be implemented by the exact shape of scan to be performed
        # only returns the waveform
        return dac_waveform.get_spiral_waveform(self.stepsize, self.n_steps, self.exptime + self.latency)


@macro
class Csnake(Cscan):
    """
    Continuous snake scan macro for the NI dac box.

    csnake <horizontal left> <horizontal right>
           <vertical bottom> <vertical top>
           <step size> <exp time>
    """

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
        N_points_per_line = int((self.dac_0_end - self.dac_0_start) / self.stepsize) + 1
        N_lines = int((self.dac_1_end - self.dac_1_start) / self.stepsize) + 1
        self.n_steps = N_points_per_line * N_lines
        self.print_progress = False
        if self.panda is None:
            raise Exception('Set DacScan.panda to your panda master')

    def _generate_waveform(self):
        # to be implemented by the exact shape of scan to be performed
        # only returns the waveform
        return dac_waveform.get_snake_waveform(self.dac_0_start, self.dac_0_end, self.dac_1_start, self.dac_1_end, self.stepsize, self.exptime + self.latency)
