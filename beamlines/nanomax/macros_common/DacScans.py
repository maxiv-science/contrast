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
    trig_high = 255 # set value in range 0-255 to activate digital output 0-7

    @classmethod
    def save_h5_file(cls, path, wf):
        wf_file = path
        # setting the triggers to low by extending the waveform length 
        wf =  np.concatenate((wf, wf[:,-1:]), axis=-1)
        wf[-1, -1] = 0
        with h5py.File(wf_file, 'w') as ofp:
            ofp.create_dataset('entry/measurement/waveform/data', data=wf, compression='gzip')

    @classmethod
    def get_spiral_wf(cls, motors, stepsize, steps, latency, exptime, step_scan):
        pixeltime = (latency + exptime)
        wf = np.zeros((5, int(steps * cls.dac_rate * pixeltime)))
        wf[0,:] = np.full(int(steps * cls.dac_rate * pixeltime), motors[0].position())
        wf[1,:] = np.full(int(steps * cls.dac_rate * pixeltime), motors[1].position())
        wf[2,:] = np.full(int(steps * cls.dac_rate * pixeltime), motors[0].position())
        # adding the digital trigger pulse train on the fifth column, operating the digital outputs p0.0 - p0.7
        trig = np.zeros(int(latency*cls.dac_rate))
        trig = np.append(trig, np.full(int(exptime*cls.dac_rate), cls.trig_high))
        triggers = np.tile(trig,steps)
        wf[4,:] = triggers

        if step_scan:
            #step scanning
            npositions = np.arange(0, steps)
            A = stepsize * np.sqrt(npositions/np.pi)
            B = np.sqrt(4 * np.pi * npositions)
            spiral_a = np.repeat(A*np.cos(B), cls.dac_rate*pixeltime)
            spiral_b = np.repeat(A*np.sin(B), cls.dac_rate*pixeltime)
        else:
            # continuous scanning
            npositions = np.arange(0, int(cls.dac_rate * steps * pixeltime))
            A = stepsize * np.sqrt(npositions/(cls.dac_rate*pixeltime*np.pi))
            B = np.sqrt(4 * np.pi * npositions/(cls.dac_rate*pixeltime))
            spiral_a = A*np.cos(B)
            spiral_b = A*np.sin(B)

        wf[motors[0].axis,:] = spiral_a
        wf[motors[1].axis,:] = spiral_b
        wf =  np.concatenate((wf, wf[:,-1:]), axis=-1)
        wf[-1, -1] = 0
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

        nsteps = int(wf_x.shape[0] / pixeltime)

        # adding the digital trigger pulse train on the fifth column, operating the digital outputs p0.0 - p0.7
        trig = np.zeros(int(latency*cls.dac_rate))
        trig = np.append(trig, np.full(int(exptime*cls.dac_rate), cls.trig_high))
        triggers = np.tile(trig,nsteps)
        wf = np.vstack([wf_x, wf_y, np.zeros(len(triggers)), np.zeros(len(triggers)), triggers])
        wf =  np.concatenate((wf, wf[:,-1:]), axis=-1)
        wf[-1, -1] = 0

        return wf, nsteps

        get_fermat_wf(self.dac_0_start, self.dac_0_end, 
                                          self.dac_1_start, self.dac_1_end,
                                          self.stepsize, self.exptime, 
                                          self.latency, self.optimize)

    
    @classmethod
    def _make_step_wf(cls, dac_positions, latency, exptime):
        """
        takes a list of dac position, the latency and the exposure time
        and creates the waveform for a waveform step scan

        dac_positions come as a 2D array with the first dimension
        being a list of 3 values: x, y and z coordinates and
        the 2nd dimension being the various scan points
        
        latency and exp time come in seconds
        """

        # number of scan points
        n_p, n_steps = np.shape(dac_positions)
        # number of sampling points in the waveform
        n_latency = int(latency * cls.dac_rate)
        n_exposure = int(exptime * cls.dac_rate)
        n_perpoint = n_latency + n_exposure

        # create position array with waveform sampling # shape [3,n]
        positions = dac_positions.repeat(n_perpoint, axis=1)
        # create the array of trigger pulses at waveform sampling # shape [1,n]
        trig = np.append(np.zeros((1, n_latency)), np.full((1, n_exposure), cls.trig_high))
        triggers = np.tile(trig, (1, n_steps))
        # create a waveform for the fourth, not used, analog output channel
        wf_dac_3 = np.zeros((1, n_steps * n_perpoint))
        # lets merge them to a waveform shape [5, n]
        wf = np.concatenate((positions, wf_dac_3, triggers), axis=0)
        # lets add one sampling point, to lower the trigger again
        wf =  np.concatenate((wf, wf[:,-1:]), axis=-1)
        wf[-1, -1] = 0

        # return the waveform (shape [5, n]) and the number of scan/data points
        return wf, n_steps

class WFtrigscan(SoftwareScan):
    """
    Base class for any step or continuous scan performed as a single waveform for the NI dac box.
    The waveform contains 4 DAC channels and a fifth column defining the trigger.  
    On purpuse this one is not a macro, so it can not be called by itself 
    """
    panda = None
    dac_0 = None
    dac_1 = None
    dac_2 = None
    p_latency = 0.0001 
    dac_rate = 1000
    trig_high = 255 # set value in range 0-255 to activate digital output 0-7
    

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
        z = self.dac_2.position()
        et = self.dac_0.proxy.get_end_time()
        print('\rEstimated finish time: %s - X:%7.3f um Y:%7.3f um Z:%7.3f um' % (et, x, y, z), end='')

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
class WFfermat(WFtrigscan):
    """
    Waveform fermat spiral step scan

    wffermat <horizontal left> <horizontal right> 
             <vertical bottom> <vertical top>
             <step size> <exp time> <latency time> <optimize>
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
        self.dac_0_start = ((float(args[0]) - self.dac_0._offset) / self.dac_0._scaling)
        self.dac_0_end   = ((float(args[1]) - self.dac_0._offset) / self.dac_0._scaling)
        self.dac_1_start = ((float(args[2]) - self.dac_1._offset) / self.dac_1._scaling)
        self.dac_1_end   = ((float(args[3]) - self.dac_1._offset) / self.dac_1._scaling)
        self.stepsize    =  (float(args[4]) / self.dac_1._scaling)
        self.exptime = float(args[5])
        self.latency = float(args[6])
        self.optimize = bool(args[7])
        self.print_progress = False
        if self.panda is None:
            raise Exception('Set DacScan.panda to your panda master')

    def _calc_2d_positions(self):
        """
        calculates x y positions
        """
        # scaling factors and angular step width
        c_0    = 0.524   # 3rd closest neighbor is on average one step away
        c      = c_0*self.stepsize
        phi    = 0.5*(1+np.sqrt(5))
        phi_0  = 2*np.pi/(1+phi)
        # center and size of the rectangular scan field
        center = [0.5*(self.dac_0_start+self.dac_0_end), 0.5*(self.dac_1_start+self.dac_1_end)] 
        size   = [np.abs(self.dac_0_start-self.dac_0_end), np.abs(self.dac_1_start-self.dac_1_end)]
        # max radius of and scan points in the spiral
        r_max  = 0.5*np.sqrt(size[0]**2+size[1]**2)
        n_max  = int(np.ceil((r_max/c)**2))
        # calculate all positions until n_max (and thus r_max)
        n      = np.linspace(0,n_max,n_max+1, endpoint=True)
        pos_1  = c*np.sqrt(n)*np.sin(n*phi_0)+center[0]
        pos_2  = c*np.sqrt(n)*np.cos(n*phi_0)+center[1]
        # remove positions outside the scan rectangle
        pos_12 = []
        for i, p1 in enumerate(pos_1):
            p2 = pos_2[i]
            if not(p1>self.dac_0_start):
                continue
            if not(p1<self.dac_0_end):
                continue
            if not(p2>self.dac_1_start):
                continue
            if not(p2<self.dac_1_end):
                continue
            pos_12.append([p1,p2])
        pos_12 = np.array(pos_12)
        # finding a short(er) scan path
        if self.optimize:
            # basically... solving the TSP problem
            best_path = self.two_opt(pos_12)
            self.pos_12 = pos_12[best_path]
        else:
            # sort on the first motor axis
            best_path = np.argsort(pos_12[:,0])
            self.pos_12 = pos_12[best_path]

    def two_opt(self, cities, improvement_threshold=0.5, max_iter=4):
        # 2-opt Algorithm adapted from https://en.wikipedia.org/wiki/2-opt
        # from https://stackoverflow.com/questions/25585401/travelling-salesman-in-scipy

        # Calculate the euclidian distance in n-space of the route r 
        # traversing cities c, ending at the path start.
        def path_distance(r,c): 
            return np.sum([np.linalg.norm(c[r[p]]-c[r[p-1]]) for p in range(len(r))])

        # Reverse the order of all elements from element i to element k in array r.
        def two_opt_swap(r,i,k): 
            return np.concatenate((r[0:i],r[k:-len(r)+i-1:-1],r[k+1:len(r)]))

        route = np.arange(cities.shape[0])
        improvement_factor = 1 
        iterations = 0
        best_distance = path_distance(route,cities) 
        while improvement_factor > improvement_threshold and iterations<max_iter: 
            distance_to_beat = best_distance 
            for swap_first in range(1,len(route)-2): 
                for swap_last in range(swap_first+1,len(route)): 
                    new_route = two_opt_swap(route,swap_first,swap_last)
                    new_distance = path_distance(new_route,cities) 
                    if new_distance < best_distance: 
                        route = new_route
                        best_distance = new_distance 
            improvement_factor = 1 - best_distance/distance_to_beat 
            iterations += 1
        return route


    def _generate_waveform(self):
        """
        create the wave form in shape of the step scanned spiral
        returns the waveform and the number of points in the scan
        """

        # caclucalte the 2D positions
        self._calc_2d_positions()
        # add a third column
        n_steps, n_p = np.shape(self.pos_12)
        dac_positions = np.concatenate((self.pos_12, np.zeros((n_steps,1))), axis=-1)
        dac_positions = dac_positions.T
        # calculate the step waveform and number of data points
        return dac_waveform._make_step_wf(dac_positions, self.latency, self.exptime)

@macro
class WFspiral(WFtrigscan):
    """
    Waveform spiral step scan

    wfspiral <motor 1> <motor 2> <step size> <positions> <exp time> <latency time>
    """

    def __init__(self, *args, **kwargs):
        """
        Parse arguments
        """
        self._command = None  # updated if run via macro
        self.scannr = env.nextScanID
        self.print_progress = True
        env.nextScanID += 1
        self.fast_axis = args[0].axis
        self.slow_axis = args[1].axis
        self.stepsize = float(args[2])
        self.n_steps = int(args[3])
        self.exptime = float(args[4])
        self.latency = float(args[5])
        self.print_progress = False
        if self.panda is None:
            raise Exception('Set DacScan.panda to your panda master')

    def _generate_waveform(self):
        """
        create the wave form in shape of the step scanned spiral
        returns the waveform and the number of points in the scan
        """
        pixeltime = (self.latency + self.exptime)
        wf = np.zeros((5, int(self.n_steps * self.dac_rate * pixeltime)))
        wf[0,:] = np.full(int(self.n_steps * self.dac_rate * pixeltime), self.dac_0.position())
        wf[1,:] = np.full(int(self.n_steps * self.dac_rate * pixeltime), self.dac_1.position())
        wf[2,:] = np.full(int(self.n_steps * self.dac_rate * pixeltime), self.dac_2.position())
        # adding the digital trigger pulse train on the fifth column, operating the digital outputs p0.0 - p0.7
        trig = np.zeros(int(self.latency*self.dac_rate))
        trig = np.append(trig, np.full(int(self.exptime*self.dac_rate), self.trig_high))
        triggers = np.tile(trig,self.n_steps)
        wf[4,:] = triggers

        n_positions = np.arange(0, self.n_steps)
        A = self.stepsize * np.sqrt(n_positions/np.pi)
        B = np.sqrt(4 * np.pi * n_positions)
        spiral_a = np.repeat(A*np.cos(B), self.dac_rate*pixeltime)
        spiral_b = np.repeat(A*np.sin(B), self.dac_rate*pixeltime)
        wf[self.fast_axis,:] = spiral_a
        wf[self.slow_axis,:] = spiral_b
        return wf, self.n_steps

@macro
class Cspiral(WFtrigscan):
    """
    Waveform spiral continuous scan

    cspiral <motor 1> <motor 2> <step size> <positions> <exp time>
    """

    def __init__(self, *args, **kwargs):
        """
        Parse arguments
        """
        self._command = None  # updated if run via macro
        self.scannr = env.nextScanID
        self.print_progress = True
        env.nextScanID += 1
        self.fast_axis = args[0].axis
        self.slow_axis = args[1].axis
        self.stepsize = float(args[2])
        self.n_steps = int(args[3])
        self.exptime = float(args[4])
        self.latency = 0.001
        self.print_progress = False
        if self.panda is None:
            raise Exception('Set DacScan.panda to your panda master')

    def _generate_waveform(self):
        """
        create the wave form in shape of the step scanned spiral
        returns the waveform and the number of points in the scan
        """
        pixeltime = (self.latency + self.exptime)
        wf = np.zeros((5, int(self.n_steps * self.dac_rate * pixeltime)))
        wf[0,:] = np.full(int(self.n_steps * self.dac_rate * pixeltime), self.dac_0.position())
        wf[1,:] = np.full(int(self.n_steps * self.dac_rate * pixeltime), self.dac_1.position())
        wf[2,:] = np.full(int(self.n_steps * self.dac_rate * pixeltime), self.dac_2.position())
        # adding the digital trigger pulse train on the fifth column, operating the digital outputs p0.0 - p0.7
        trig = np.zeros(int(self.latency*self.dac_rate))
        trig = np.append(trig, np.full(int(self.exptime*self.dac_rate), self.trig_high))
        triggers = np.tile(trig,self.n_steps)
        wf[4,:] = triggers

        n_positions = np.arange(0, int(self.dac_rate * self.n_steps * pixeltime))
        A = self.stepsize * np.sqrt(n_positions/(self.dac_rate*pixeltime*np.pi))
        B = np.sqrt(4 * np.pi * n_positions/(self.dac_rate*pixeltime))
        spiral_a = A*np.cos(B)
        spiral_b = A*np.sin(B)
        wf[self.fast_axis,:] = spiral_a
        wf[self.slow_axis,:] = spiral_b
        return wf, self.n_steps

@macro
class WFsnake(WFtrigscan):
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

@macro
class Csnake(WFtrigscan):
    """
    Waveform snake continuous scan

    csnake <horizontal left> <horizontal right> <steps>
            <vertical bottom> <vertical top> <steps>
            <exp time>
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
        self.latency = 0.001
        self.print_progress = False
        if self.panda is None:
            raise Exception('Set DacScan.panda to your panda master')

    def _generate_waveform(self):
        """
        create the wave form in shape of the continuously scanned snake
        returns the waveform and the number of points in the scan
        """
        return dac_waveform.get_snake_wf(self.dac_0_start, self.dac_0_end, self.steps_x, 
                                         self.dac_1_start, self.dac_1_end, self.steps_y,
                                         self.latency, self.exptime, False)


