"""
Module helping with changing the energy at the NanoMAX beamline. 
So far only providing information about the energy calibration
"""

import os
import numpy as np
from contrast.environment import env, macro, register_shortcut, runCommand

#   ToDo
#       - get it all automated:
#           - table values for ivu_gap and monox2per
#           - being able to switch off and on nanobpm beam stearing
#           - auto tuning scans of ivu gap


@macro
class change_energy(object):
    """
    Helps to set the energy of the beamline.
    So far only advises about the difference between the 'energy' motor
    and the actual photon energy as calibrated using known absorption edges.
    """

    ######################################################################################################
    #   energy calibration data
    #   data:  /data/staff/nanomax/commissioning_2020-1/20200218-energy-calibration/raw/energycalibration
    #   elogy: https://elogy.maxiv.lu.se/logbooks/358/entries/19587/
    ######################################################################################################

                    #foil   #literature   #measured
    data_20200218 = [['Zn',   9659,        9636.0],
                     ['Cr',   5989,        5987.0],
                     ['Zr',  17998,       17857.0],
                     ['Mo',  20000,       19821.0],
                     ['Se',  12658,       12597.0],
                     ['Ni',   8333,        8316.5],
                     ['Fe',   7112,        7103.5],
                     ['Au',  11919,      11871.25]]
    # Mono Si-111 -> d = 3.1355 Å
    d_Si111_in_A = 3.1355

    ############################################################################
    #   methods
    ############################################################################

    def __init__(self, set_energy_to=None, verbosity=3):
        self.set_energy_to = set_energy_to
        self.verbosity     = verbosity
        self.fit_calibration_data()

    def fit_calibration_data(self):
        # fit these calibration values with simple polynomials
        self.lit_energies_in_eV      = np.array([x[1] for x in self.data_20200218])
        self.mea_energies_in_eV      = np.array([x[2] for x in self.data_20200218])
        self.fit_parameters_lit2meas = np.polyfit(x   = self.lit_energies_in_eV, 
                                                  y   = self.mea_energies_in_eV, 
                                                  deg = 2)
        self.fit_parameters_meas2lit = np.polyfit(x   = self.mea_energies_in_eV, 
                                                  y   = self.lit_energies_in_eV, 
                                                  deg = 2)

    def run_command(self, command):
        runCommand(command)

    def get_current_energy(self):
        runCommand('wms energy')
        self.curr_energy_motor = env.lastMacroResult
        self.curr_energy_calib = np.polyval(p = self.fit_parameters_meas2lit, 
                                            x = self.curr_energy_motor)

    def show_current_energy(self):
        print('#'*80)
        print('# currently:')
        print('#     energy motor: ', round(self.curr_energy_motor, 2), 'eV')
        print('# corresponds to a real')
        print('#     photon energy:', round(self.curr_energy_calib, 2), 'eV')
        print('#'*80)

    def estiamte_where_to_go(self):
        self.goal_energy_motor = np.polyval(p = self.fit_parameters_lit2meas, 
                                            x = self.set_energy_to)

    def show_estimate(self):
        print('#'*80)
        print('# if you want to go to:')
        print('#     photon energy:', round(self.set_energy_to, 2), 'eV')
        print('# you will have to go to about')
        print('#     energy motor: ', round(self.goal_energy_motor, 2), 'eV')
        print('# which is',round(self.goal_energy_motor-self.set_energy_to, 2), 'eV off')
        print('#'*80)

    def run(self):
        if self.set_energy_to == None:
            # user did not give any energy
            # -> show current energy instead
            self.get_current_energy()
            self.show_current_energy()

        elif not(isinstance(self.set_energy_to, (int, float))):
            print('no number given')

        elif (self.set_energy_to < 6000) or (self.set_energy_to > 28000):
            print('you try to reach an energy we can not reach')

        else:
            # user wants to go to a given energy 
            # -> show him where to put the energy motor according to the
            #    energy calibration
            self.estiamte_where_to_go()
            self.show_estimate()
