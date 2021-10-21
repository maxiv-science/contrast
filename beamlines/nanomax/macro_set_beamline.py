"""
Macro for setting energy, monochromator motors, slits etc in a convenient way
Ulf Johansson 2021-05-24
"""

import numpy as np
import math
import os
import sys
from contrast.environment import env, macro, register_shortcut, runCommand

@macro
class SetEnergy(object):
    """
    Sets the monochromator motors (energy and crystal separation), the SSA, the undulator and mirror coating with respect to energy
    
    setenergy <energy> <ssa> 

    usage / examples:
        %set_energy 12300                               - sets the monochromator energy and undulator gap
        %set_energy 10000 ssa='coh'                     - sets the monochromator energy, undulator gap and ssa size
        %set_energy 7000 ssa='flux' set_coating=True    - sets the monochromator energy, undulator gap, ssa size and hfm mirror coating
        %set_energy 7000 set_gap=False    - sets the monochromator energy 
    """

    ############################################################################
    #   
    ############################################################################


    def __init__(self, energy=None, ssa='', set_gap=True, set_coating=False, verbosity=3):
        # Constants
        self.h = 6.62606896E-34 # Plank's constant
        self.e = 1.602176565E-19 # electron charge
        self.c = 299792458 # speed of light
        self.d = 3.1356E-10 # Si(111) crystal lattice spacing
        self.bo = 1E-2 # beam offset
        self.gap_offset = 0.04
        self.coatings = {'Si':'-10.5', 'Rh':'-1.4', 'Pt':'9.5'}
        self.energy = energy
        self.ssa=ssa
        self.set_gap = set_gap
        self.set_coating = set_coating
        self.verbosity = verbosity
        self.pit_rol = {
                    5:(-0.2260,-0.0008),
                    6:(-0.2252,-0.0003),
                    7:(-0.2245,0.0002),
                    8:(-0.2238,0.0006),
                    9:(-0.2232,0.0011),
                    10:(-0.2228,0.0016),
                    11:(-0.2223,0.0021),
                    12:(-0.2219,0.0025),
                    13:(-0.2215,0.0030),
                    14:(-0.2211,0.0036),
                    15:(-0.2208,0.0042),
                    16:(-0.2205,0.0048),
                    17:(-0.2203,0.0053),
                    18:(-0.2201,0.0058),
                    19:(-0.2199,0.0063),
                    20:(-0.2197,0.0068),
                    21:(-0.2196,0.0074),
                    22:(-0.2195,0.0080),
                    23:(-0.2195,0.0086),
                    24:(-0.2193,0.0090),
                    25:(-0.2191,0.0094),
                    26:(-0.2190,0.0099),
                    27:(-0.2189,0.0104),
                    28:(-0.2188,0.0109)
                    }    

        # table with undulator gaps and harmonics
        self.ivu_energy_gap = [
                    [5000,4.544,3],
                    [5100,4.607,3],
                    [5200,4.668,3],
                    [5300,4.730,3],
                    [5400,4.792,3],
                    [5500,4.854,3],
                    [5600,4.916,3],
                    [5700,4.977,3],
                    [5800,5.040,3],
                    [5900,5.102,3],
                    [6000,5.164,3],
                    [6100,5.227,3],
                    [6200,5.289,3],
                    [6300,5.352,3],
                    [6400,5.415,3],
                    [6500,5.479,3],
                    [6600,5.542,3],
                    [6700,5.606,3],
                    [6800,5.670,3],
                    [6900,5.734,3],
                    [7000,5.799,3],
                    [7100,5.863,3],
                    [7200,5.929,3],
                    [7300,5.994,3],
                    [7400,6.060,3],
                    [7500,6.127,3],
                    [7600,6.193,3],
                    [7700,6.261,3],
                    [7800,6.329,3],
                    [7900,6.397,3],
                    [8000,6.466,3],
                    [8100,6.535,3],
                    [8200,6.605,3],
                    [8300,6.676,3],
                    [8400,6.748,3],
                    [8500,4.607,5],
                    [8600,4.643,5],
                    [8700,4.680,5],
                    [8800,4.718,5],
                    [8900,4.755,5],
                    [9000,4.792,5],
                    [9100,4.829,5],
                    [9200,4.866,5],
                    [9300,4.903,5],
                    [9400,4.941,5],
                    [9500,4.977,5],
                    [9600,5.015,5],
                    [9700,5.052,5],
                    [9800,5.090,5],
                    [9900,5.127,5],
                    [10000,5.164,5],
                    [10100,5.202,5],
                    [10200,5.239,5],
                    [10300,5.276,5],
                    [10400,5.314,5],
                    [10500,5.352,5],
                    [10600,5.390,5],
                    [10700,5.428,5],
                    [10800,5.466,5],
                    [10900,5.504,5],
                    [11000,5.542,5],
                    [11100,5.580,5],
                    [11200,5.619,5],
                    [11300,5.657,5],
                    [11400,5.695,5],
                    [11500,5.734,5],
                    [11600,5.773,5],
                    [11700,4.553,7],
                    [11800,4.580,7],
                    [11900,4.607,7],
                    [12000,4.633,7],
                    [12100,4.659,7],
                    [12200,4.685,7],
                    [12300,4.713,7],
                    [12400,4.739,7],
                    [12500,4.765,7],
                    [12600,4.792,7],
                    [12700,4.818,7],
                    [12800,4.845,7],
                    [12900,4.872,7],
                    [13000,4.898,7],
                    [13100,4.925,7],
                    [13200,4.951,7],
                    [13300,4.977,7],
                    [13400,5.004,7],
                    [13500,5.031,7],
                    [13600,5.058,7],
                    [13700,5.085,7],
                    [13800,5.111,7],
                    [13900,5.138,7],
                    [14000,5.164,7],
                    [14100,5.191,7],
                    [14200,5.218,7],
                    [14300,5.245,7],
                    [14400,5.271,7],
                    [14500,5.298,7],
                    [14600,5.325,7],
                    [14700,5.352,7],
                    [14800,5.379,7],
                    [14900,5.406,7],
                    [15000,5.433,7],
                    [15100,4.565,9],
                    [15200,4.586,9],
                    [15300,4.607,9],
                    [15400,4.627,9],
                    [15500,4.647,9],
                    [15600,4.668,9],
                    [15700,4.689,9],
                    [15800,4.710,9],
                    [15900,4.730,9],
                    [16000,4.751,9],
                    [16100,4.771,9],
                    [16200,4.792,9],
                    [16300,4.812,9],
                    [16400,4.833,9],
                    [16500,4.854,9],
                    [16600,4.875,9],
                    [16700,4.895,9],
                    [16800,4.916,9],
                    [16900,4.936,9],
                    [17000,4.957,9],
                    [17100,4.977,9],
                    [17200,4.998,9],
                    [17300,5.019,9],
                    [17400,5.040,9],
                    [17500,5.061,9],
                    [17600,5.082,9],
                    [17700,5.102,9],
                    [17800,5.123,9],
                    [17900,5.144,9],
                    [18000,5.164,9],
                    [18100,5.185,9],
                    [18200,5.206,9],
                    [18300,5.227,9],
                    [18400,5.248,9],
                    [18500,4.573,11],
                    [18600,4.590,11],
                    [18700,4.607,11],
                    [18800,4.623,11],
                    [18900,4.640,11],
                    [19000,4.657,11],
                    [19100,4.674,11],
                    [19200,4.690,11],
                    [19300,4.708,11],
                    [19400,4.724,11],
                    [19500,4.741,11],
                    [19600,4.758,11],
                    [19700,4.775,11],
                    [19800,4.792,11],
                    [19900,4.809,11],
                    [20000,4.825,11],
                    [20100,4.842,11],
                    [20200,4.859,11],
                    [20300,4.876,11],
                    [20400,4.893,11],
                    [20500,4.910,11],
                    [20600,4.927,11],
                    [20700,4.944,11],
                    [20800,4.961,11],
                    [20900,4.977,11],
                    [21000,4.994,11],
                    [21100,5.011,11],
                    [21200,5.029,11],
                    [21300,5.046,11],
                    [21400,5.063,11],
                    [21500,5.080,11],
                    [21600,5.097,11],
                    [21700,5.114,11],
                    [21800,5.131,11],
                    [21900,4.578,11],
                    [22000,4.592,13],
                    [22100,4.607,13],
                    [22200,4.621,13],
                    [22300,4.635,13],
                    [22400,4.649,13],
                    [22500,4.663,13],
                    [22600,4.677,13],
                    [22700,4.692,13],
                    [22800,4.706,13],
                    [22900,4.721,13],
                    [23000,4.735,13],
                    [23100,4.749,13],
                    [23200,4.763,13],
                    [23300,4.778,13],
                    [23400,4.792,13],
                    [23500,4.806,13],
                    [23600,4.820,13],
                    [23700,4.834,13],
                    [23800,4.849,13],
                    [23900,4.863,13],
                    [24000,4.878,13],
                    [24100,4.892,13],
                    [24200,4.906,13],
                    [24300,4.920,13],
                    [24400,4.935,13],
                    [24500,4.949,13],
                    [24600,4.964,13],
                    [24700,4.977,13],
                    [24800,4.992,13],
                    [24900,5.006,13],
                    [25000,5.021,13],
                    [25100,4.557,15],
                    [25200,4.569,15],
                    [25300,4.582,15],
                    [25400,4.594,15],
                    [25500,4.607,15],
                    [25600,4.619,15],
                    [25700,4.631,15],
                    [25800,4.643,15],
                    [25900,4.656,15],
                    [26000,4.668,15],
                    [26100,4.680,15],
                    [26200,4.693,15],
                    [26300,4.705,15],
                    [26400,4.718,15],
                    [26500,4.730,15],
                    [26600,4.742,15],
                    [26700,4.755,15],
                    [26800,4.767,15],
                    [26900,4.780,15],
                    [27000,4.792,15],
                    [27100,4.804,15],
                    [27200,4.816,15],
                    [27300,4.829,15],
                    [27400,4.841,15],
                    [27500,4.854,15],
                    [27600,4.866,15],
                    [27700,4.879,15],
                    [27800,4.891,15],
                    [27900,4.903,15],
                    [28000,4.916,15],
                    [28100,4.928,15],
                    [28200,4.941,15],
                    [28300,4.953,15],
                    [28400,4.965,15],
                    [28500,4.977,15],
                    [28600,4.574,17],
                    [28700,4.585,17],
                    [28800,4.595,17],
                    [28900,4.607,17],
                    [29000,4.618,17],
                    [29100,4.628,17],
                    [29200,4.639,17],
                    [29300,4.650,17],
                    [29400,4.661,17],
                    [29500,4.672,17],
                    [29600,4.682,17],
                    [29700,4.694,17],
                    [29800,4.705,17]        
                    ] 

    def run(self):
        command = 'umv' 
        if isinstance(self.energy, (int, float)):
            if self.energy < 5000 or self.energy >28250:
                print('     [Error] photon energy must be between 5000 and 28250 eV')
                exit()

            # Sets the monochromator perpendicular, coarse pitch and coarse roll motors
            per = self.beam_offset()
            pit, rol = self.mono_x2_pit_rol()
            if per < -0.2 or per > 1.0 or pit < -1.0 or pit > 1.0 or rol < -1.0 or rol > 1.0:
                    print('    [ERROR] Tries to set per, pit or rol to unreasonable value %.3f %.3f %.3f' %(per,pit,rol))
            else:
                command += ' energy %0.2f' % (self.energy)
                command += ' mono_x2per %.3f' % (per)
                #command += ' mono_x2pit %.4f' % (pit) + ' mono_x2rol %.4f' % (rol)
            
            # Sets the SSA opening
            if isinstance(self.ssa, (str)):
                sx, sy = self.ssa_gap_coherent()
                if self.ssa == 'coh':
                    command += ' ssa_gapx %.2f' % (sx) + ' ssa_gapy %.2f' % (sy)
                elif self.ssa == 'flux':
                    command += ' ssa_gapx %.2f' % (2*sx) + ' ssa_gapy %.2f' % (2*sy)

            # Finds the best undulator gap
            if self.set_gap:
                gap = self.ivu_gap()
                if gap < 4.5 or gap > 7.0:
                    print('    [ERROR] Tries to set undulator to unreasonable value %.3f' %gap)
                else:
                    command += ' ivu_gap %0.3f' % (gap)
                    ivu_command = 'umv ivu_gap %0.3f' % (gap)             

            # Selects mirror coating on the HFM mirror
            if self.set_coating:
                if self.energy < 10000:
                    command += ' hfm_y ' + self.coatings['Si']
                elif self.energy < 22000:
                    command += ' hfm_y ' + self.coatings['Rh']
                elif self.energy < 28250:
                    command += ' hfm_y ' + self.coatings['Pt']
            print('Remember to pause the NanoBPM before changing energy. \n\nCommand to execute: ' + command + '\n')
            if input('Execute(y/n)?').lower().strip() == 'y':
                runCommand(command)
                if self.set_gap:
                    runCommand(ivu_command)
                print('Beamline set to %.2f eV'% self.energy)     
            else:
                print('No motors were moved')    
        else:
            print('    [ERROR] photon energy is not specified')

    def wavelength(self):
        # Wavelength in meter returned
        return self.h*self.c/(self.e*self.energy)

    def bragg(self):
        # Bragg in degrees returned
        return math.degrees(math.asin(self.wavelength()/(2*self.d)))

    def beam_offset(self):
        # Crystal separation value with zero value at 10000 eV is returned
        return 1E3*(self.bo/(2*math.cos(math.radians(self.bragg())))-0.005100678469508198)

    def ssa_gap_coherent(self):
        # SSA coherent value returned in micrometer, as a tuple
        sx = 1E6*self.wavelength()*46.82/(2*225E-6)
        sy = 1E6*self.wavelength()*46.69/(2*378E-6)
        return sx, sy

    def mono_x2_pit_rol(self):
        # Returns motor positions for mono pitch and roll coarse motors, as a tuple
        return self.pit_rol[self.energy//1000.0]
        
    def ivu_gap(self):
        le = 0
        he = 30000
        lg = 25
        hg = 25
        lh = 0
        hh = 0
        for e, g,h in self.ivu_energy_gap:
            if e <= self.energy and e >= le:
                if e == le and g > lg:
                    pass
                else:
                    le = e
                    lg = g
                    lh = h

        for e, g, h in self.ivu_energy_gap:
            if e > self.energy and e <= he:
                if e== he and g < hg:
                    pass
                else:
                    he = e
                    hg = g
                    hh = h

        # interpolate to find gap
        gap = (hg-lg)/float(he-le)*(self.energy-le)+lg
        gap += self.gap_offset
        #print((le, lg, lh), (he, hg, hh), gap, sep=' ')
        return gap

    def kb_info(self):
        # Enter energy in eV, returns focus size and focus depth, as a tuple
        foc_size = 0.443*self.wavelength()/6.1E-4
        foc_depth = self.wavelength()/(6.1E-4**2)
        return foc_size, foc_depth



