
import os
import numpy as np
from contrast.environment import macro, register_shortcut, runCommand

@macro
class attenuate(object):
    """
    Sets the attenuators to absorb X percent of the beam depending 
    on the current photon beam enegery.
    """
    def __init__(self, attenuate_to=None, how='safe', verbosity=3):
        self.attenuate_to = attenuate_to
        self.how          = how
        self.verbosity    = verbosity

        self.load_settings()
        self.load_absorption_data()

    def load_settings(self):
        # status 2019-10-06
        self.elements  = ['Al', 'Ti', 'Si', 'Cu', None, 'Fe', 'Mo', 'Ta', 'Ag']
        self.position  = [-40000, -29000, -18000, -9000, 0, 
                           11000,  21000,  33000, 41000]
        self.carriers  = ['att_1', 'att_2', 'att_3', 'att_4'] 
        self.thickness = [[  25,   50,  100,  100],   # in um
                          [  20,   40,   80,  160],
                          [ 250,  500, 1000, 1000],
                          [  20,   40,   80,  160],
                          [   0,    0,    0,    0],
                          [  50,  100,  200,  400],
                          [  15,   30,   60,  120],
                          [  20,   40,   80,  160],
                          [  25,   50,  100,  200]]
        self.thickness = np.array(self.thickness)

    def load_absorption_file(self, fpath):
        return np.loadtxt(fpath, skiprows=2)

    def load_absorption_data(self):
        # loading offline data between 5 and 25 keV 
        # taken from http://henke.lbl.gov/optical_constants/filter2.html
        self.absorption_data = {}
        base  = os.path.dirname(os.path.realpath(__file__))                     #fixme: might change
        base += '/attenuation/attenuation_1um_'
        for element in [x for x in self.elements if not(x==None)]:
            fpath = base + element + '.txt'
            data  = self.load_absorption_file(fpath)
            self.absorption_data[element] = data

    def get_current_energy(self):
        self.photon_energy = 12000                                              #fixme: get energy information from the beamline

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
        self.T_tot = [[T1*T2*T3*T4, i1, i2, i3, i4] 
                      for i1, T1 in enumerate(self.transmission[:,0])  
                      for i2, T2 in enumerate(self.transmission[:,1]) 
                      for i3, T3 in enumerate(self.transmission[:,2])  
                      for i4, T4 in enumerate(self.transmission[:,3]) ] 
        self.T_tot = np.array(self.T_tot)
        self.T_tot = self.T_tot[np.argsort(self.T_tot[:,0])]

    def run(self):
        
        self.get_current_energy()
        self.calculate_transmission_of_1um()
        self.calculate_transmission_of_actual_foils()
        self.calcualte_possible_permutations()
        
        # return the solution for the next smallest possible transmission
        try:
            closest_result = list(filter(lambda i: i[0] <= 1-self.attenuate_to, 
                                         self.T_tot))[-1]
            # returns a list of 5 elements: achievable T and the 4 motor settings
            #print(closest_result)

            commands = []
            if self.verbosity>=3 or self.how=='safe':
                print('aimed for:')
                print('    absorption  ', self.attenuate_to)
                print('    transmission', 1-self.attenuate_to)
                print('    at currently', self.photon_energy, 'eV')
                print('can achieve:')
                print('    absorption  ', str(1-closest_result[0])[:5])
                print('    transmission', str(closest_result[0])[:5])
                print('with motor setting:')

                for i_carrier, i_pos in enumerate(closest_result[1:]):
                    i_pos    = int(i_pos)

                    command  = 'mv ' + str(self.carriers[i_carrier])
                    command += ' ' + str(self.position[i_pos]).ljust(8)
                    commands.append(command)
                    line  = '    ' + command

                    line += '#' + str(self.thickness[i_pos, i_carrier]).rjust(5)
                    line += ' um of ' + str(self.elements[i_pos])
                    print(line)

            if self.how=='safe':
                yes = ['yes', 'y', '1', 'true']
                user_input =  input('Proceed to move motrors? [Y/n] ').lower()
                if user_input in yes:
                    for command in commands:
                        print(command)                                              #fixme: actually run the commands
            else:
                for command in commands:
                        print(command)                                              #fixme: actually run the commands

        except:
            print('absorption of', self.attenuate_to, 
                  'cannot be reached safely')
