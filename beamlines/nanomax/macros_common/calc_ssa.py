
"""
A macro to calculate the SSA settings needed for coherent / incohernet beam
at either the diffraction or the imaging endstation.
"""

import os
import numpy as np
from contrast.environment import env, macro, register_shortcut, runCommand


@macro
class Calc_SSA(object):
    """
    Calculate the SSA settings needed for coherent / incohernet beam
    at either the diffraction (D) or the imaging (I) endstation.

    %calc_ssa <endstation D/I> <coherent_beam> optional: <FZP_diameter_in_um>

    usage / examples:
        %calc_ssa D False     # calculates the SSA setting for a high-flux beam
                              # at the current energy at the diffraction
                              # endstation
        %calc_ssa I True 75   # calculates the SSA setting for a fully coherent
                              # beam at the current energy at the imaging
                              # endstation for a FZP of 75um diameter
    """

    def __init__(self, endstation=None, coherent=True, FZP_diameter_um=None):
        self.endstation = endstation
        self.coherent = coherent
        self.FZP_diameter_um = FZP_diameter_um
        self.accepted_names_D = ['D', 'd', 'Diffraction', 'diffraction', 'KB']
        self.accepted_names_I = ['I', 'i', 'Imaging', 'imaging', 'FZP']

    def input_validation(self):
        if not (self.endstation in self.accepted_names_D
                or self.endstation in self.accepted_names_I):
            print("    [ERROR] No correct endstation given.")
            print("            Use 'D' for the diffraction endstation.")
            print("            Use 'I' for the imaging endstation.")
            return False
        elif (self.endstation in self.accepted_names_I
              and not (isinstance(self.FZP_diameter_um, (int, float)))):
            print("    [ERROR] The FZP diameter is not given as a number.")
            return False
        else:
            return True

    def get_current_energy(self):
        runCommand('wms energy')
        # print(env)
        self.photon_energy_eV = env.lastMacroResult
        self.wavelength_m = 12400. / self.photon_energy_eV * 1e-10

    def get_distance_from_ssa(self):
        if self.endstation in self.accepted_names_D:
            self.d_ssa_m = 46.7
        elif self.endstation in self.accepted_names_I:
            self.d_ssa_m = 35.0

    def get_acceptance(self):
        if self.endstation in self.accepted_names_D:
            self.accepteance_m = np.array([225.e-6, 379.e-6])
        elif self.endstation in self.accepted_names_I:
            acc = [1e-6 * self.FZP_diameter_um, 1e-6 * self.FZP_diameter_um]
            self.accepteance_m = np.array(acc)

    def print_result(self):
        print('    photon energy: '+str(self.photon_energy_eV)+' eV')
        print('    distance from SSA: '+str(self.d_ssa_m)+' m')
        print('    optics aperture: '+str(self.accepteance_m)+' m')
        if self.coherent:
            print('    beam: coherence mode')
        else:
            print('    beam: high flux mode')
        print('-'*20)
        print('    required SSA opening:',
              "ssa_gapx {0:.2f}".format(self.ssa_opening_m[0]*1.e6),
              "ssa_gapy {0:.2f}".format(self.ssa_opening_m[1]*1.e6))

    def run(self):
        if self.input_validation():

            # collect inputs
            self.get_current_energy()
            self.get_distance_from_ssa()
            self.get_acceptance()

            # calculate the ssa opening (s)
            self.ssa_opening_m = (self.wavelength_m * self.d_ssa_m
                                  / 2. / self.accepteance_m)
            if not(self.coherent):
                self.ssa_opening_m = 2 * self.ssa_opening_m

            # return results
            self.print_result()
