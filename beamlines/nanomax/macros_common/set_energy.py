"""
Macro for setting energy, monochromator motors, slits etc in a convenient way
Ulf Johansson 2023-10-02
"""

import numpy as np
import math
import os
import sys
from contrast.environment import env, macro, register_shortcut, runCommand


@macro
class SetEnergy(object):
    """
    Sets the monochromator motors (energy and crystal separation), the
    SSA, the undulator and mirror coating with respect to energy

    setenergy <energy> <ssa>

    usage / examples:
        %setenergy 12300
           - sets the monochromator energy and undulator gap

        %setenergy 10000 ssa='coh'
            - sets the monochromator energy, undulator gap and ssa size

        %setenergy 7000 ssa='flux' set_coating=True
            - sets the monochromator energy, undulator gap, ssa size and
              hfm mirror coating

        %setenergy 7000 set_gap=False
            - sets the monochromator energy

        %setenergy 7000 only_display=True
            - displays motion command but no actual motor motions


    """

    def __init__(self, energy=None, ssa='', set_gap=True, set_coating=False, 
            only_display=False, verbosity=3):
        # Constants
        self.h = 6.62606896e-34   # Plank's constant
        self.e = 1.602176565e-19  # electron charge
        self.c = 299792458        # speed of light
        self.d = 3.1356e-10       # Si(111) crystal lattice spacing
        self.bo = 1e-2            # beam offset
        self.gap_offset = 0.00
        self.coatings = {'Si': '-10.5', 'Rh': '-1.4', 'Pt': '9.5'}
        self.energy = energy
        self.ssa = ssa
        self.set_gap = set_gap
        self.set_coating = set_coating
        self.only_display = only_display
        self.verbosity = verbosity

        fpath = os.path.dirname(os.path.realpath(__file__))
        self.ivu_energy_gap = np.loadtxt(fpath + '/bl_tables/energy_gap.txt', skiprows = 2)
        self.pit_rol = np.loadtxt(fpath + '/bl_tables/pit_rol.txt', skiprows = 2)

    def run(self):
        command = 'umv'
        if isinstance(self.energy, (int, float)):
            if self.energy < 5000 or self.energy > 28250:
                msg = '[Error] photon energy must be between 5000 and 28250 eV'
                print('     %s' % msg)
                exit()

            # Sets the monochromator perpendicular, coarse pitch and
            # coarse roll motors
            per = self.beam_offset()
            pit, rol = self.mono_x2_pit_rol()
            if (per < -0.2 or per > 1.0
                    or pit < -1.0 or pit > 1.0
                    or rol < -1.0 or rol > 1.0):
                msg = 'Tries to set per, pit or rol to unreasonable value'
                print('    [ERROR] %s %.3f %.3f %.3f' % (msg, per, pit, rol))
            else:
                command += ' energy %0.2f' % (self.energy)
                command += ' mono_x2per %.3f' % (per)

            # Sets the SSA opening
            if isinstance(self.ssa, (str)):
                sx, sy = self.ssa_gap_coherent()
                if self.ssa == 'coh':
                    command += ' ssa_gapx %.2f' % sx + ' ssa_gapy %.2f' % sy
                elif self.ssa == 'flux':
                    command += (' ssa_gapx %.2f' % (2 * sx)
                                + ' ssa_gapy %.2f' % (2 * sy))

            # Finds the best undulator gap
            if self.set_gap:
                gap = self.ivu_gap()
                if gap < 4.5 or gap > 7.0:
                    msg = 'Tries to set undulator to unreasonable value'
                    print('    [ERROR] %s %.3f' % (msg, gap))
                else:
                    command += ' ivu_gap %0.3f' % (gap)

            # Selects mirror coating on the HFM mirror
            if self.set_coating:
                if self.energy < 10000:
                    command += ' hfm_y ' + self.coatings['Si']
                elif self.energy < 22000:
                    command += ' hfm_y ' + self.coatings['Rh']
                elif self.energy < 28250:
                    command += ' hfm_y ' + self.coatings['Pt']
            print('\nCommand: ' + command + '\n')
            if self.only_display == False:
                runCommand(command)
                print('Beamline set to %.2f eV' % self.energy)
            else:
                print('No motors were moved')
        else:
            print('    [ERROR] photon energy is not specified')

    def wavelength(self):
        # Wavelength in meter returned
        return self.h * self.c / (self.e * self.energy)

    def bragg(self):
        # Bragg in degrees returned
        return math.degrees(math.asin(self.wavelength() / (2 * self.d)))

    def beam_offset(self):
        # Crystal separation value with zero value at 10000 eV is returned
        return 1e3 * (self.bo / (2 * math.cos(math.radians(self.bragg())))
                      - 0.005100678469508198)

    def ssa_gap_coherent(self):
        # SSA coherent value returned in micrometer, as a tuple
        sx = 1e6 * self.wavelength() * 46.82 / (2 * 225e-6)
        sy = 1e6 * self.wavelength() * 46.69 / (2 * 378e-6)
        return sx, sy

    def mono_x2_pit_rol(self):
        # Returns motor positions for mono pitch and roll coarse motors
        e_diff = self.energy
        for i in self.pit_rol:
            e_d = abs(i[0] - self.energy)
            if  e_d < e_diff:
                e_diff = e_d
                ret = i[1:]
        return ret             

    def ivu_gap(self):
        le = 0
        he = 30000
        lg = 25
        hg = 25
        lh = 0
        hh = 0
        for e, g, h in self.ivu_energy_gap:
            if e <= self.energy and e >= le:
                if e == le and g > lg:
                    pass
                else:
                    le = e
                    lg = g
                    lh = h

        for e, g, h in self.ivu_energy_gap:
            if e > self.energy and e <= he:
                if e == he and g < hg:
                    pass
                else:
                    he = e
                    hg = g
                    hh = h
        
        # interpolate to find gap
        gap = (hg - lg) / float(he - le) * (self.energy - le) + lg
        gap += self.gap_offset
        print(le, he, lg, hg, lh, hh, gap)
        return gap

    def kb_info(self):
        # Enter energy in eV, returns focus size and focus depth, as a tuple
        foc_size = 0.443 * self.wavelength() / 6.1e-4
        foc_depth = self.wavelength() / (6.1e-4**2)
        return foc_size, foc_depth
