"""
This module contains code for running a fake STXM scan using either the
finex/finey or the coarsex/coarsey motors. The scanned motors are moved,
and fake data generated from a stock image are made available once each
line is complete.
"""

from contrast.environment import macro, MacroSyntaxError
from contrast.motors import Motor, DummyMotor, all_are_motors
from contrast.recorders import active_recorders, RecorderHeader, RecorderFooter
from contrast.environment import env
from dummy_detector import get_stxm_signal
from collections import OrderedDict
import numpy as np
import time


def wait_for_motor(motor, prnt=False):
    while motor.busy():
        time.sleep(.01)
        if prnt:
            print('%s: %.2f'
                  % (motor.name, motor.user_position) + '\r', end='')


@macro
class StxmScan(object):
    """
    Dummy STXM scan:

        stxmscan <xmotor> <startx> <stopx> <Nx>
                 <ymotor> <starty> <stopy> <Ny> <exp_time>

    Nx and Ny are intervals, which generates Nx scan measurements at
    Ny+1 positions.
    """

    def __init__(self, *args, stop_event=None, **kwargs):
        self.stop_event = stop_event
        self._command = None
        self.scannr = env.nextScanID
        env.nextScanID += 1
        try:
            self.x_motor, self.x_min, self.x_max, self.x_intervals = args[0:4]
            self.y_motor, self.y_min, self.y_max, self.y_intervals = args[4:8]
            self.exptime = args[8]
            assert self.x_motor.name in ['finex', 'coarsex']
            assert self.y_motor.name in ['finey', 'coarsey']
            assert self.x_max > self.x_min
            assert self.y_max > self.y_min
            assert all_are_motors((self.x_motor, self.y_motor))
        except:
            raise MacroSyntaxError

    def run(self):
        try:
            self._run()
        except KeyboardInterrupt:
            print('scan interrupted!')
            for r in active_recorders():
                r.queue.put(RecorderFooter(scannr=self.scannr,
                                           status='interrupted',
                                           path=env.paths.directory))

    def _run(self):
        t0 = time.time()
        print('\nScan #%d starting at %s' % (self.scannr, time.asctime()))

        # send a header to the recorders
        snap = env.snapshot.capture()
        for r in active_recorders():
            r.queue.put(RecorderHeader(scannr=self.scannr,
                                       status='started',
                                       path=env.paths.directory,
                                       snapshot=snap,
                                       description=self._command))

        # start the scan loop
        old_vel = self.x_motor.velocity
        em = [m for m in DummyMotor.getinstances() if m.name == 'energy'][0]
        energy = em.dial_position
        for iy, y in enumerate(
            np.linspace(self.y_min, self.y_max, self.y_intervals + 1)):

            # there might be a stop flag
            if self.stop_event and self.stop_event.is_set():
                raise KeyboardInterrupt

            # just to be realistic, move the motors to the start of the line
            t1 = time.time()
            self.y_motor.dial_position = y
            self.x_motor.dial_position = self.x_min
            wait_for_motor(self.y_motor, prnt=True)
            wait_for_motor(self.x_motor, prnt=True)

            # start the line scan
            t2 = time.time()
            vel = (np.abs(self.x_min - self.x_max)
                   / self.x_intervals
                   / self.exptime)
            self.x_motor.velocity = vel
            self.x_motor.dial_position = self.x_max

            # meanwhile, work out the offsets from the other motors
            if self.x_motor.name == 'finex':
                x_offset_motor_name = 'coarsex'
            else:
                x_offset_motor_name = 'finex'
            if self.y_motor.name == 'finey':
                y_offset_motor_name = 'coarsex'
            else:
                y_offset_motor_name = 'finex'
            x_offset = [m for m in Motor.getinstances() if m.name == x_offset_motor_name][0].dial_position
            y_offset = [m for m in Motor.getinstances() if m.name == y_offset_motor_name][0].dial_position

            # and work out what the data should be - average along trajectory
            line = []
            endpoints = np.linspace(self.x_min, self.x_max, self.x_intervals + 1)
            for i in range(len(endpoints) - 1):
                inds = np.arange(endpoints[i], endpoints[i + 1])
                inds += x_offset
                line.append(np.mean([get_stxm_signal(y + y_offset, ix, energy) for ix in inds]))
            line = np.array(line)

            # now wait for the motor to finish moving
            wait_for_motor(self.x_motor, prnt=True)
            self.x_motor.velocity = old_vel
            t3 = time.time()

            # put some stuff in recorders
            dt = time.time() - t0
            dct = OrderedDict()
            dct[self.y_motor.name] = y
            dct[self.x_motor.name] = endpoints[:-1]
            dct['stxm_det'] = np.array(line)
            dct['dt'] = dt
            for r in active_recorders():
                r.queue.put(dct)

            # print something
            print('line %u done, t=%.1fs (line %.2fs, return %.2fs)' % (iy, dct['dt'], t3-t2, t2-t1))

        # tell the recorders that the scan is over
        for r in active_recorders():
            r.queue.put(RecorderFooter(scannr=self.scannr,
                                       status='finished',
                                       path=env.paths.directory,
                                       snapshot=snap,
                                       description=self._command))
