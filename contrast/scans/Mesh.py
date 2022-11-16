from .Scan import SoftwareScan
from ..environment import macro, MacroSyntaxError
from ..motors import all_are_motors
import numpy as np
import time

import matplotlib.pyplot as plt


@macro
class Mesh(SoftwareScan):
    """
    Software scan on a regular grid of N motors. ::

        mesh <motor1> <start> <stop> <intervals> ... <exp_time>

    optional keyword arguments:
        jitter: float ... Randomizes perfect grid positions.
    """

    def __init__(self, *args, **kwargs):
        self.motors = []
        self.limits = []
        self.intervals = []
        self.kwargs = kwargs

        try:
            exposuretime = float(args[-1])
            super(Mesh, self).__init__(exposuretime)
            for i in range(int((len(args) - 1) / 4)):
                self.motors.append(args[4 * i])
                self.limits.append(
                    [float(m) for m in args[4 * i + 1:4 * i + 3]])
                self.intervals.append(int(args[4 * i + 3]))
            self.n_positions = np.prod(np.array(self.intervals) + 1)
            assert all_are_motors(self.motors)
            assert (len(args) - 1) % 4 == 0
        except:
            raise MacroSyntaxError

    def _generate_positions(self):
        positions = []
        for i in range(len(self.motors)):
            positions.append(np.linspace(self.limits[i][0],
                                         self.limits[i][1],
                                         self.intervals[i] + 1))
        grids = np.meshgrid(*reversed(positions))
        grids = [l_ for l_ in reversed(grids)]  # fastest last

        if 'jitter' in self.kwargs.keys():
            print('[!] jittered grid postions by factor:',
                  self.kwargs['jitter'])
            if self.kwargs['jitter'] != 0:

                step_sizes = []
                for i, motor in enumerate(self.motors):
                    d = np.abs(self.limits[i][0] - self.limits[i][1])
                    n = self.intervals[i]
                    step_sizes.append(1. * d / n)

                rel_jitter = np.random.uniform(low=-.5 * self.kwargs['jitter'],
                                               high=.5 * self.kwargs['jitter'],
                                               size=np.shape(grids))
                for i, step_size in enumerate(step_sizes):
                    grids[i] += rel_jitter[i] * step_size

        for i in range(len(grids[0].flat)):
            yield {m.name: pos.flat[i] for (m, pos) in zip(self.motors, grids)}


@macro
class DMesh(Mesh):
    """
    Software scan on a regular grid of N motors, with positions relative
    to each motor's current one. Moves motors back at the end. ::

        dmesh <motor1> <start> <stop> <intervals> ... <exp_time>
    """
    def _generate_positions(self):
        current = {m.name: m.position() for m in self.motors}
        for pos in super(DMesh, self)._generate_positions():
            for i, m in enumerate(self.motors):
                pos[m.name] += current[m.name]
            yield pos

    def run(self):
        old_pos = [m.position() for m in self.motors]
        super(DMesh, self).run()
        # wait for motors then move them back
        while True in [m.busy() for m in self.motors]:
            time.sleep(.01)
        print('Returning motors to their starting positions...')
        for m, pos in zip(self.motors, old_pos):
            m.move(pos)
        while True in [m.busy() for m in self.motors]:
            time.sleep(.01)
        print('...done')

@macro
class MeshJMesh(SoftwareScan):
    """
    2D Software scan for NearField ptychography.
    Each point of a larger 2D mesh scan is another smaller 2D mesh.
        
        meshjmesh <motor1> <abs_start1>     <abs_stop1>     <nr_int1>     <jit_amp1> 
                           <rel_start_sub1> <rel_stop_sub1> <nr_int_sub1> <jit_amp_sub1>
                  <motor1> <abs_start2>     <abs_stop2>     <nr_int2>     <jit_amp2> 
                           <rel_start_sub2> <rel_stop_sub2> <nr_int_sub2> <jit_amp_sub2>
                  <exposure_time>

    The start and stop position of the coarse mesh are in aboslute coordinates,
    while the start and stop positions of the submesh are relative coordiantes.

    2nd axis is the fast axis.
    """

    def __init__(self, m1, l1_l, l1_u, n1, j1, sl1_l, sl1_u, sn1, sj1, 
                       m2, l2_l, l2_u, n2, j2, sl2_l, sl2_u, sn2, sj2,
                       exptime, **kwargs):
        try:
            SoftwareScan.__init__(self, float(exptime))

            self.m1 = m1       # ax1 - motor
            self.l1_l = l1_l   # coarse mesh - lower limit
            self.l1_u = l1_u   # coarse mesh - upper limit
            self.n1 = n1       # coarse mesh - number of intervals
            self.j1 = j1       # coarse mesh - rel. jitter amplitude ... [0,1]
            self.sl1_l = sl1_l # fine mesh - lower limit
            self.sl1_u = sl1_u # fine mesh - upper limit
            self.sn1 = sn1     # fine mesh - number of intervals
            self.sj1 = sj1     # fine mesh - rel. jitter amplitude ... [0,1]

            self.m2 = m2       # ax2 - motor
            self.l2_l = l2_l   # coarse mesh - lower limit
            self.l2_u = l2_u   # coarse mesh - upper limit
            self.n2 = n2       # coarse mesh - number of intervals
            self.j2 = j2       # coarse mesh - rel. jitter amplitude ... [0,1]
            self.sl2_l = sl2_l # fine mesh - lower limit
            self.sl2_u = sl2_u # fine mesh - upper limit
            self.sn2 = sn2     # fine mesh - number of intervals
            self.sj2 = sj2     # fine mesh - rel. jitter amplitude ... [0,1]

            self.exptime = exptime
            self.kwargs = kwargs

            self.motors = [m1, m2]
            self.limits = [[l1_l+sl1_l, l1_u+sl1_u], [l2_l+sl2_l, l2_u+sl2_u]]

            self.calc_positions()
            self.n_positions = int(len(self.pos_12))
            assert all_are_motors(self.motors)
        except:
            raise MacroSyntaxError

    def calc_positions(self):
        
        grid_1_coarse = np.linspace(self.l1_l, self.l1_u, self.n1+1)
        grid_1_fine = np.linspace(self.sl1_l, self.sl1_u, self.sn1+1)
        stepsize_1_coarse = 1.* np.abs(self.l1_u-self.l1_l) / (1. * self.n1)
        stepsize_1_fine = 1.* np.abs(self.sl1_u-self.sl1_l) / (1. * self.sn1)

        grid_2_coarse = np.linspace(self.l2_l, self.l2_u, self.n2+1)
        grid_2_fine = np.linspace(self.sl2_l, self.sl2_u, self.sn2+1)
        stepsize_2_coarse = 1.* np.abs(self.l2_u-self.l2_l) / (1. * self.n2)
        stepsize_2_fine = 1.* np.abs(self.sl2_u-self.sl2_l) / (1. * self.sn2)

        print(stepsize_1_coarse)
        print(stepsize_1_fine)
        print(stepsize_2_coarse)
        print(stepsize_2_fine)

        # calculate the absolute coarse mesh grid
        p12_coarse = []
        for i, p1 in enumerate(grid_1_coarse):
            for j, p2 in enumerate(grid_2_coarse):
                p12_coarse.append([p1, p2])
        p12_coarse = np.array(p12_coarse)

        # put the coarse jitter on the the coarse mesh grid
        rjc = np.random.uniform(low=-.5, high=.5, size=np.shape(p12_coarse))
        for i, p12 in enumerate(p12_coarse):
            p12_coarse[i] = [p12[0] + rjc[i,0] * self.j1 * stepsize_1_coarse,
                             p12[1] + rjc[i,1] * self.j2 * stepsize_2_coarse]

        # calculate the fine grid on top of that coarse mesh grid
        p12_fine = []
        for k, pc in enumerate(p12_coarse):
            p1c, p2c = pc
            for i, p1 in enumerate(grid_1_fine):
                for j, p2 in enumerate(grid_2_fine):
                    p12_fine.append([p1c + p1, p2c + p2])
        p12_fine = np.array(p12_fine)

        # put the fine jitter on the the fine mesh grid
        rjf = np.random.uniform(low=-.5, high=.5, size=np.shape(p12_fine))
        for i, p12 in enumerate(p12_fine):
            p12_fine[i] = [p12[0] + rjf[i,0] * self.sj1 * stepsize_1_fine,
                           p12[1] + rjf[i,1] * self.sj2 * stepsize_2_fine]

        # plot the positions if requested
        if 'plot' in self.kwargs.keys():
            if self.kwargs['plot']:
                n = len(p12_fine[:,0])
                c = np.linspace(0, 1, n)

                plt.figure()
                plt.plot(p12_fine[:,0], p12_fine[:,1], lw=1, c='k', alpha=0.5)
                plt.scatter(p12_fine[:,0], p12_fine[:,1], c=c)
                plt.xlabel(str(self.m1.name))
                plt.ylabel(str(self.m2.name))

                title = 'meshjmesh\n'
                title += f'{str(self.m1.name)}    {self.l1_l} {self.l1_u} {self.n1} {self.j1}      '
                title += f'{self.sl1_l} {self.sl1_u} {self.sn1} {self.sj1}\n'
                title += f'{str(self.m2.name)}    {self.l2_l} {self.l2_u} {self.n2} {self.j2}      '
                title += f'{self.sl2_l} {self.sl2_u} {self.sn2} {self.sj2}\n'
                title += f'{self.exptime}'

                plt.title(title)
                plt.tight_layout()
                plt.show()

        # return the positions
        self.pos_12 = p12_fine

    def _generate_positions(self):
        for i, pos in enumerate(self.pos_12):
            yield {self.motors[0].name: pos[0],
                   self.motors[1].name: pos[1]}