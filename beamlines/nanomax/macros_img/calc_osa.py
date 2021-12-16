"""
A macro to calculate the maximum working distance and corresponding OSA size
for a given set of Frensnel zone plate, central stop and photon energy.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from contrast.environment import env, macro, register_shortcut, runCommand

@macro
class Calc_OSA(object):
    """
    Calculate the maximum distance of the OSA from the sample and the corresponding size
    of the OSA. From there smaller and larger OSA diameters are possible if the OSA is 
    placed closer to the sample. Those possibilities can be read from a created plot.
    If an OSA diameter / position is given, the positioning possibilities will be checked.
    Any problems with the positioning will be pointed out and solutions will be offered.

    %calc_osa <FZP_diameter_um> <FZP_drn_nm> <CS_diamter_um> <photon_energy_keV>
    
    optional:
        + <OSA_diameter_um (default=None)> <OSA_distance_mm (default=None)>

    usage / examples:
        %calc_osa 75 100 30 8          # calculates the OSA possibilites for a Fresnel zone plate
                                       # with 75 um diameter, 100 nm outer most zone width, a 
                                       # central stop of 30 um diameter at 8 keV photon energy
                                       
        %calc_osa 75 100 30 8 5 None   # ...
                                       # and will tell you where a 5 um diameter OSA can be placed
                                       
        %calc_osa 75 100 30 8 None 1   # ... 
                                       # and will tell you what OSA sizes would be possible for
                                       # a placement 1 mm upstream from the focus                             
  
        %calc_osa 75 100 30 8 5 1      # ... 
                                       # and will check if a 5 um OSA at 1 mm from the focus will do,
                                       # and if not tell you what you could change
  
    """

    def __init__(self, FZP_diameter_um   = 75,
                       FZP_drn_nm        = 100,
                       CS_diameter_um     = 20,
                       photon_energy_keV = 8,
                       OSA_diameter_um   = None,
                       OSA_distance_mm   = None):
        
        self.FZP_diameter_um   = FZP_diameter_um
        self.FZP_drn_nm        = FZP_drn_nm
        self.CS_diamter_um     = CS_diameter_um
        self.photon_energy_keV = photon_energy_keV
        self.OSA_diameter_um   = OSA_diameter_um
        self.OSA_distance_mm   = OSA_distance_mm
        self.N_rays = 100

    def input_validation(self):
        if not(isinstance(self.FZP_diameter_um, (int, float))):
            print("    [ERROR] The FZP diameter was not given as a number.")
            return False
        elif not(isinstance(self.FZP_drn_nm, (int, float))):
            print("    [ERROR] The outer most zone width was not given as a number.")
            return False
        elif not(isinstance(self.CS_diamter_um, (int, float))):
            print("    [ERROR] The central stop diameter was not given as a number.")
            return False
        elif not(isinstance(self.photon_energy_keV, (int, float))):
            print("    [ERROR] The photon energy not given as a number.")
            return False
        elif not(isinstance(self.OSA_diameter_um, (int, float)) or self.OSA_diameter_um==None):
            print("    [ERROR] Give an OSA diameter as a number, or NONE")
            return False
        elif isinstance(self.OSA_diameter_um, (int, float)) and self.OSA_diameter_um>=self.CS_diamter_um:
            print("    [ERROR] the given OSA is larger than the given central stop")
            return False
        elif not(isinstance(self.OSA_distance_mm, (int, float)) or self.OSA_distance_mm==None):
            print("    [ERROR] Give an OSA distance as a number, or NONE")
            return False   
        else:
            return True

    def print_input(self):
        print('calculating for:')
        print('    photon energy:         %.3f keV' % self.photon_energy_keV)
        print('    central stop diameter: %.3f um' % self.CS_diamter_um)
        print('    FZP diameter:          %.3f um' % self.FZP_diameter_um)
        print('    outer most zone width: %.3f nm' % self.FZP_drn_nm)
        if self.OSA_diameter_um!=None:
            print('    OSA diameter:          %.3f um' % self.OSA_diameter_um)
        if self.OSA_distance_mm!=None:
            print('    OSA distance:          %.3f mm' % self.OSA_distance_mm)
            

    def print_result_max_distance(self):
        print('    '+'-'*20)
        print('    focal length:          %.3f mm' % self.f1_mm)
        print('    '+'-'*20)
        print('    maximal OSA distance:  %.3f mm' % self.f_OSA_max_mm)
        print('    osa diameter for that: %.3f um' % self.d_OSA_max_um)
        if self.d_OSA_max_um>self.CS_diamter_um:
            print('WARNING: CS too small')   
        print('    '+'-'*20)

    def plot_result(self):
        self.fig = plt.figure(figsize=(12,8), facecolor='white')
        plt.subplot(1,1,1)
        
        # plot CS
        plt.plot([-1.5*self.f1_mm, -1.5*self.f1_mm], [-0.5*self.CS_diamter_um, 0.5*self.CS_diamter_um], c='k', lw=5)
        
        # plot FZP
        plt.plot([-1.*self.f1_mm, -1.*self.f1_mm], [-0.5*self.FZP_diameter_um, 0.5*self.FZP_diameter_um], c='k', lw=5)
        
        
        d_det = 33
        
        # plot incoming beam and 1st order focus
        for y in list(np.linspace(0.5*self.FZP_diameter_um, -0.5*self.FZP_diameter_um, self.N_rays, endpoint=True))+[-0.5*self.CS_diamter_um, 0.5*self.CS_diamter_um]:
            if np.abs(y) >= 0.5*self.CS_diamter_um:
                ys = [y, y, 0, -y, -y*d_det/self.f1_mm]
                xs = [-2.*self.f1_mm, -1.*self.f1_mm, 0, 1*self.f1_mm, d_det]
            else:
                ys = [y,y,]
                xs = [-2.*self.f1_mm, -1.5*self.f1_mm]
            plt.plot(xs, ys, lw=1, c='k', alpha=0.5)

        # plot 2nd order focus
        # Todo... have rays blocked by the OSA (or not)
        for y in list(np.linspace(0.5*self.FZP_diameter_um, -0.5*self.FZP_diameter_um, self.N_rays, endpoint=True))+[-0.5*self.CS_diamter_um, 0.5*self.CS_diamter_um]:
            if np.abs(y) >= 0.5*self.CS_diamter_um:
                #ys = [y, 0, -y, -y-y*d_det/self.f2_mm]
                #xs = [-1.*self.f1_mm, -1.*self.f1_mm+self.f2_mm, -1.*self.f1_mm+2.*self.f2_mm, d_det]
                ys = [y, 0, -y]
                xs = [-1.*self.f1_mm, -1.*self.f1_mm+self.f2_mm, -1.*self.f1_mm+2.*self.f2_mm]
                plt.plot(xs, ys, lw=1, c='b', alpha=0.5)
            
        # plot OSA
        plt.plot([-self.OSA_distance_mm, -self.OSA_distance_mm], [ 0.5*self.FZP_diameter_um,  0.5*self.OSA_diameter_um], c='r', lw=5)
        plt.plot([-self.OSA_distance_mm, -self.OSA_distance_mm], [-0.5*self.FZP_diameter_um, -0.5*self.OSA_diameter_um], c='r', lw=5)

        #axes
        plt.axhline(y=0, c='k', alpha=0.3, lw=1)
        plt.axvline(x=0, c='k', alpha=0.3, lw=1)
        #plt.xlim([-1.7*self.f1_mm, 1.0*self.f1_mm])
        #plt.ylim([-0.6*self.FZP_diameter_um, 0.6*self.FZP_diameter_um])
        
        plt.xlim([-2*self.OSA_distance_mm, self.OSA_distance_mm])
        plt.ylim([-self.OSA_diameter_um, self.OSA_diameter_um])
        plt.ylabel('transverse in [um]')
        plt.xlabel('longitudinal in [mm]')
        plt.grid(which='both')
        
        plt.tight_layout()
        plt.show()

    def calc_max_distance(self): 
        f1_um    = 1000.*self.f1_mm
        f2_um    = 1000.*self.f2_mm
        rFZP_um  =   0.5*self.FZP_diameter_um
        rCS_um   =   0.5*self.CS_diamter_um
        x_intersect_um    = (rCS_um+rFZP_um)/((rFZP_um/f1_um)+(rCS_um/f2_um))
        self.f_OSA_max_mm = -x_intersect_um/1000+self.f1_mm
        self.d_OSA_max_um = 2*self.f_OSA_max_mm*1000*rFZP_um/f1_um    
        self.print_result_max_distance()
    
    def calc_suggestions(self):
        self.suggested_distance_mm  = 0
        if self.OSA_diameter_um!=None:
            # calculating maximum distance for a given OSA size
            if self.OSA_diameter_um <= self.d_OSA_max_um:
                # danger of cutting the 1st order
                self.suggested_distance_mm = 1.*self.f_OSA_max_mm*self.OSA_diameter_um/self.d_OSA_max_um
            elif self.OSA_diameter_um >= self.d_OSA_max_um:
                # danger of letting some of the 2nd order through
                self.suggested_distance_mm = 1.*(self.CS_diamter_um-self.OSA_diameter_um)*self.f_OSA_max_mm/(self.CS_diamter_um-self.d_OSA_max_um)
            
        self.suggested_diameters_um = [0,0]
        if self.OSA_distance_mm!=None:
            # calculating possible diameters for the given distance
            self.suggested_diameters_um[0] = self.d_OSA_max_um/self.f_OSA_max_mm* self.OSA_distance_mm
            self.suggested_diameters_um[1] = self.CS_diamter_um-(self.CS_diamter_um-self.d_OSA_max_um)/self.f_OSA_max_mm*self.OSA_distance_mm
    
    def print_suggested_distance(self):
        print('you can put your OSA maximally %.3f mm from the focus' % self.suggested_distance_mm)
    
    def print_suggested_diameters(self):
        print('at this distance your OSA should be')
        print('    at least %.3f um in diameter and ' % self.suggested_diameters_um[0])
        print('    maximally %.3f um in diameter' % self.suggested_diameters_um[1])
        
    def run(self):
        if self.input_validation():

            # print input
            self.print_input()
         
            # some basic calculations
            self.photon_wavelength_m = 12.4/self.photon_energy_keV*1.e-10
            self.f1_mm               = 1.e-12*self.FZP_diameter_um*self.FZP_drn_nm/self.photon_wavelength_m  
            # ToDo ... maybe a more acurate calcualtion that does not require "many" zones
            self.f2_mm               = 0.5*self.f1_mm 
        
            # calculate the maximal OSA distance and corresponding size
            self.calc_max_distance()

            # calcualte possible distances / sizes on given OSA parameters
            self.calc_suggestions()
            
            # now acting on what the user has given as OSA parameters
            if self.OSA_diameter_um==None and self.OSA_distance_mm==None:
                #the user did not specify OSA parameters to test
                self.OSA_diameter_um = 1.*self.d_OSA_max_um
                self.OSA_distance_mm = 1.*self.f_OSA_max_mm
                self.plot_result()
            
            elif self.OSA_diameter_um!=None and self.OSA_distance_mm==None:
                #the user only has given a size, ... so wants to know a good distance
                self.print_suggested_distance()
                self.OSA_distance_mm = 1.*self.suggested_distance_mm
                self.plot_result()
                
            elif self.OSA_diameter_um==None and self.OSA_distance_mm!=None:
                #the user only has given a disance, ... so wants to know a good size/region
                if self.OSA_distance_mm > self.f_OSA_max_mm:
                    print('[WARNING] with these settings, no OSA can be that far away from the focus!')
                    print('          choose a distance smaller than %.3f mm' % self.f_OSA_max_mm)
                else:
                    self.print_suggested_diameters()
                    self.OSA_diameter_um = 1.*self.suggested_diameters_um[0]
                    self.plot_result()
            
            elif self.OSA_diameter_um!=None and self.OSA_distance_mm!=None:
                #the user has a specific OSA diameter AND distance to test
                if self.OSA_diameter_um >= self.CS_diamter_um:
                    print('[WARNING] your OSA is too large to be used!')
                elif self.OSA_distance_mm >= self.f_OSA_max_mm:
                    print('[WARNING] your OSA is too far away from the focus!')
                    self.print_suggested_distance()
                else:
                    # checking if the given distance cuts the 1st oder
                    if (self.CS_diamter_um-self.d_OSA_max_um)/self.f_OSA_max_mm > (self.CS_diamter_um-self.OSA_diameter_um)/self.OSA_distance_mm:
                        print('[WARNING] your OSA is letting some of the 2nd order through!')
                        print('          move your OSA closer to the focus') 
                        self.print_suggested_distance()
                        print('          or choose a smaller OSA')
                        self.print_suggested_diameters()
                        self.plot_result()
                    # checking if the given distance lets some of the 2nd order through
                    elif self.d_OSA_max_um/self.f_OSA_max_mm > self.OSA_diameter_um/self.OSA_distance_mm:
                        print('[WARNING] your OSA is cutting into the beam!')
                        self.print_suggested_distance()
                        self.plot_result()
                    else:
                        # everthing seems to be fine
                        self.plot_result()        
