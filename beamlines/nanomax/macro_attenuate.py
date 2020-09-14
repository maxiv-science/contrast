"""
Module providing a macro to automatically absorb X percent of the
beam using the absorbers at the NanoMAX beamline
"""

import os
import numpy as np
from contrast.environment import env, macro, register_shortcut, runCommand

#   ToDo
#       - avoid elements with absorption edges close to the current energy
#       - way of printing the closest possible absorption values

@macro
class attenuate(object):
    """
    Sets the attenuators to absorb X percent of the beam depending 
    on the current photon beam enegery.

    usage / examples:
        %attenuate                  # show current attenuator setting / value
        %attenuate 0.2              # attenuate to 20% beam intensity
        %attenuate 0.1 ['Si','Al']  # attenuate to 10% but only use Si and Al
                                    # ['Al','Ti','Si','Cu','Fe','Mo','Ta','Ag'] 
        %attenuate 0.2 how='unsafe' # attenuate to 20% beam intensity without
                                    # manually confirming the motor movement
                                    # ... for the usement in macros
    """

    ############################################################################
    #   absorber settings at the NanoMAX beamline - status 2019-10-06 
    ############################################################################

    elements  = ['Al', 'Ti', 'Si', 'Cu', None, 'Fe', 'Mo', 'Ta', 'Ag']
    position  = [-40000, -29000, -18000, -9000, 0, 11000,  21000,  33000, 41000]
    carriers  = ['attenuator1_x', 'attenuator2_x', 
                 'attenuator3_x', 'attenuator4_x'] 
    thickness = [[  25,   50,  100,  100],   # in um
                 [  20,   40,   80,  160],
                 [ 250,  500, 1000, 1000],
                 [  20,   40,   80,  160],
                 [   0,    0,    0,    0],
                 [  50,  100,  200,  400],
                 [  15,   30,   60,  120],
                 [  20,   40,   80,  160],
                 [  25,   50,  100,  200]]
    thickness = np.array(thickness)

    ############################################################################
    #   loading offline data between 5 and 25 keV 
    #   taken from http://henke.lbl.gov/optical_constants/filter2.html
    ############################################################################

    absorption_data = {}
    base  = os.path.dirname(os.path.realpath(__file__))
    base += '/attenuation/attenuation_1um_'
    for element in [x for x in elements if not(x==None)]:
        fpath = base + element + '.txt'
        data  = np.loadtxt(fpath, skiprows=2)
        absorption_data[element] = data

    ############################################################################
    #   methods
    ############################################################################

    def __init__(self, attenuate_to=None, use_ele=['Al', 'Ti', 'Si', 'Cu', 'Fe', 'Mo', 'Ta', 'Ag'], how='safe', verbosity=3):
        self.attenuate_to = attenuate_to
        self.how          = how
        self.verbosity    = verbosity
        self.use_ele      = use_ele
        self.use_ele.append(None)

    def get_current_energy(self):
        runCommand('wms energy')
        #print(env)
        self.photon_energy = env.lastMacroResult

    def calculate_transmission_of_1um(self):
        # linear interpolation of T(E) in log log 
        self.transmission_1um = {}
        for element in [x for x in self.elements if not(x==None)]:
            T_log = np.interp(x  = np.log(self.photon_energy),
                              xp = np.log(self.absorption_data[element][:,0]),
                              fp = np.log(self.absorption_data[element][:,1]))
            self.transmission_1um[element] = np.exp(T_log)

    def calculate_transmission_of_actual_foils(self):
        self.transmission = 1.*np.ones_like(self.thickness)
        for i, element in enumerate(self.elements):
            for j, carrier in  enumerate(self.carriers):
                if not(element==None):
                    d_um    = self.thickness[i,j]
                    T       = (self.transmission_1um[element])**d_um
                    self.transmission[i,j] = 1.*T

    def calcualte_possible_permutations(self):
        self.T_tot = [[T1*T2*T3*T4, i1, i2, i3, i4, 
                       [self.elements[i1], self.elements[i2], 
                        self.elements[i3], self.elements[i4]]] 
                      for i1, T1 in enumerate(self.transmission[:,0])  
                      for i2, T2 in enumerate(self.transmission[:,1]) 
                      for i3, T3 in enumerate(self.transmission[:,2])  
                      for i4, T4 in enumerate(self.transmission[:,3]) ] 
        self.T_tot = np.array(self.T_tot)
        self.T_tot = self.T_tot[np.argsort(self.T_tot[:,0])]

    def run_command(self, command):
        runCommand(command)

    def get_current_carrier_positions(self):
        carrier_positions = []
        for carrier in sorted(self.carriers):
            runCommand('wms '+carrier)
            carrier_positions.append(env.lastMacroResult)
        return np.array(carrier_positions)

    def estiamte_carrier_index(self, position):
        array = np.asarray(self.position)
        idx = (np.abs(array - position)).argmin()
        return idx

    def show_current_attenuation(self, printing=True):
        carrier_positions = self.get_current_carrier_positions()
        carrier_indices   = np.array([self.estiamte_carrier_index(pos) for 
                                      pos in carrier_positions])
        self.get_current_energy()
        self.calculate_transmission_of_1um()
        self.calculate_transmission_of_actual_foils()
        self.T_currently  = 1
        for j, i in enumerate(carrier_indices):
            self.T_currently *= self.transmission[i,j]
        
        if printing:
            print('currently:')
            print('    absorption  ', str(1-self.T_currently))
            print('    transmission', str(self.T_currently))
            print('with:')
            for i_carrier, i_pos in enumerate(carrier_indices):
                i_pos = int(i_pos)
                line  = '    ' + self.carriers[i_carrier]
                line += ' '+ str(carrier_positions[i_carrier]).rjust(10)
                line += ' #' + str(self.thickness[i_pos, i_carrier]).rjust(5)
                line += ' um of ' + str(self.elements[i_pos])
                print(line)

    def input_validation(self):
        if self.attenuate_to == None:
            self.show_current_attenuation()
            return False
        elif not(isinstance(self.attenuate_to, (int, float))):
            print('no number given as attenuation value')
            return False
        else:
            return True

    def check_possible_permutations_for_elements(self):
        self.T_allowed = []
        for permutation in self.T_tot:
            works = 0
            for have_to_use in permutation[5]:
                if have_to_use in self.use_ele: works+=1
            if works == len(permutation[5]):
                self.T_allowed.append(permutation)
        self.T_allowed = np.array(self.T_allowed)

    def run(self):
        if self.input_validation():

            self.get_current_energy()
            self.calculate_transmission_of_1um()
            self.calculate_transmission_of_actual_foils()
            self.calcualte_possible_permutations()
            self.check_possible_permutations_for_elements()

            self.T_min = 1.*self.T_allowed[0,0]

            try:
                if self.attenuate_to == 'max':
                    print('choosing maximal possible attenuation')
                    self.T_choosen    = 1.*self.T_allowed[0,:]
                    self.attenuate_to = 1.-self.T_choosen[0]

                # is the choosen absorption value reachable?
                elif  ((self.attenuate_to > 1) or 
                     (round(1-self.T_min,3 ) <= self.attenuate_to)):
                    print('absorption of', self.attenuate_to, 
                          'cannot be reached')
                    print('instead choosing maximum possible attenuation')
                    self.T_choosen = 1.*self.T_allowed[0,:]

                # which combination gives the closest result?
                else:
                    self.T_choosen = list(filter(lambda i: i[0] <= 1-self.attenuate_to, 
                                                 self.T_allowed))[-1]
            except ValueError:
                print("Oops!  That was no valid input")

            # get needed mv motor commands
            commands = []
            for i_carrier, i_pos in enumerate(self.T_choosen[1:1+len(self.carriers)]):
                i_pos    = int(i_pos)
                command  = 'mv ' + str(self.carriers[i_carrier])
                command += ' ' + str(self.position[i_pos]).ljust(8)
                commands.append(command)

            # print an output
            if self.verbosity>=3 or self.how=='safe':
                print('aimed for:')
                print('    absorption  ', self.attenuate_to)
                print('    transmission', max(0, 1-self.attenuate_to))
                print('    at currently', self.photon_energy, 'eV')
                print('can achieve:')
                print('    absorption  ', str(1-self.T_choosen[0]))
                print('    transmission', str(self.T_choosen[0]))
                print('with motor setting:')

                for i_carrier, i_pos in enumerate(self.T_choosen[1:1+len(self.carriers)]):
                    i_pos = int(i_pos)
                    line  = '    ' + commands[i_carrier]
                    line += '#' + str(self.thickness[i_pos, i_carrier]).rjust(5)
                    line += ' um of ' + str(self.elements[i_pos])
                    print(line)

            # move motors
            if self.how=='safe':
                yes = ['yes', 'y', '1', 'true']
                user_input = input('Proceed to move motors? [Y/n] ').lower()
                if user_input in yes:

                    # run all motor movement commands
                    for command in commands: self.run_command(command)

                    # check that the motors have moved to the calculated position
                    self.show_current_attenuation(printing=False)
                    if self.T_currently != self.T_choosen[0]:
                        print('\x1b[0;49;91[ERROR] mattenuation was NOT set\x1b[0m')
                    else:
                        print('\x1b[0;49;92msuccessfully set the attenuation\x1b[0m')

            else:                                      
                for command in commands: self.run_command(command)
