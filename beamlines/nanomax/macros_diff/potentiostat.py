"""
This module adds some basic potentiostat functionality, namely it adds
the applied potential as a motor, and provides a macro for doing cyclic
voltammetry.

These classes works with the EC301 Tango server,
https://gitlab.maxiv.lu.se/alebjo/dev-maxiv-ec301/
"""

from contrast.motors.TangoAttributeMotor import TangoAttributeMotor
from contrast.environment import macro, env
from contrast.recorders import active_recorders, RecorderHeader, RecorderFooter
import matplotlib.pyplot as plt
import tango
import time
import numpy as np


class EC301Motor(TangoAttributeMotor):
    """
    Simple motor interface to the EC301 potentiostat, controlled via:
    https://gitlab.maxiv.lu.se/alebjo/dev-maxiv-ec301/
    """

    def __init__(self, device='test/alebjo/ec301', **kwargs):
        super().__init__(device, attribute='voltage', **kwargs)

    @property
    def dial_position(self):
        return super().dial_position

    @dial_position.setter
    def dial_position(self, pos):
        self.proxy.setPotential(pos)


@macro
class Cyclic_Voltammetry():
    """
    cyclic_voltammetry t0 E0 E1 E2 rate cycles

    Does, plots, and records a cyclic voltammogram.
    """
    def __init__(self, t0, E0, E1, E2, v, cycles):
        self.args = ' '.join(map(str, [t0, E0, E1, E2, v, cycles, False]))
        print(self.args)
        self.dev = tango.DeviceProxy('test/alebjo/ec301')
        self.scannr = env.nextScanID
        env.nextScanID += 1

    def run(self):
        # Set up and tell the recorders what's about to happen
        print('Running CV, scan #%u...' % self.scannr)
        for r in active_recorders():
            r.queue.put(RecorderHeader(scannr=self.scannr,
                                       status='started',
                                       path=env.paths.directory,
                                       description=self._command))

        # Do the CV, get and record the data
        self.dev.potentialCycle(self.args)
        plt.ion()
        fig, ax = plt.subplots(nrows=2)
        fig.suptitle('Scan #%d' % self.scannr)
        plt.setp(ax[0], 'xlabel', 't', 'ylabel', 'E')
        plt.setp(ax[1], 'xlabel', 'E', 'ylabel', 'I')
        done = False
        t, E, I = [], [], []
        try:
            while not done:
                done = not self.dev.running
                nE = len(E)
                nI = len(I)
                nt = len(t)
                n = max(0, min(nE, nI, nt)-1)
                E += list(self.dev.readout_E(nE))
                I += list(self.dev.readout_I(nI))
                t += list(self.dev.readout_t(nt))
                m = min(len(E), len(I), len(t))
                ax[0].plot(t[n:m], E[n:m], 'k')
                ax[1].plot(E[n:m], I[n:m], 'r')
                plt.pause(.5)
        except KeyboardInterrupt:
            self.dev.stop()
        print('...done')

        for r in active_recorders():
            r.queue.put({'I': np.array(I), 't': np.array(t), 'E': np.array(E)})
            r.queue.put(RecorderFooter(scannr=self.scannr,
                                       status='finished',
                                       path=env.paths.directory,
                                       description=self._command))


pot = EC301Motor(name='pot')
