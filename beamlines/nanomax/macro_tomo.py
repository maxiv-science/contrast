"""
Macro to define a virtual rotation axis of the sr motor by following with
sx+basex, sy+basey and sz+basez.
"""

import os
import datetime
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
from contrast.environment import env, macro, register_shortcut, runCommand

@macro
class Tomo(object):
    """
    Sets a virtual rotation axis for the sr rotation stage mounted on top of
    the scanner. Rotational movements will be corrected by basex/y/z, the 
    scanner will be centered to sx=sy=sz=0 and the sample will be in the FOV.

    usage / examples:
        %tomo 'add_pos'     saves the current motor positions assuming the 
                            sample is centered in the FOV at this rotation
                            angle

        %tomo 'analyze'     plots all recorded data points and the sin/cos
                            fit through all data points 

        %tomo 20            will rotate the sr stage to the position 20 deg,
                            center the scanner at 0 in all three axes and
                            follow with all three base motors according to
                            their individual sin/cos fits.

        %tomo 20 assume_xz_circle=True 
                            will also rotate to 20 deg, but assume that the
                            sample moves in a circle in the x-z-plane. The
                            movement for the z-position will hence be caluclated 
                            as a cosine-movment according to the sin-fit of the 
                            x-direction and z-value of the first saved position.
                            (for when the z-position at each angle is 
                            diffcult / impossible to determine) 

        %tomo 'fpath'       prints the path to the currently used config file
    """

    ############################################################################
    #   
    ############################################################################

    def __init__(self, arg=None, assume_xz_circle=False, verbosity=3):
        self.motors = ['basex', 'basey', 'basez', 'sx', 'sy', 'sz', 'sr']
        self.arg = arg
        self.assume_xz_circle = assume_xz_circle
        self.verbosity = verbosity
        self.set_fpath()
        self.read_config_file()

    def run(self):
        if isinstance(self.arg, (int, float)):
            self.analyze()
            self.move()        
        elif isinstance(self.arg, (str));
            if self.arg == 'add_pos' or self.arg == '+':
                self.read_current_positions()
            elif self.arg == 'analyze':
                self.analyze()
                self.plot_fits()
            elif self.arg == 'fpath':
                self.print_fpath()
            else:
                print('    [ERROR] argument is an unexpected string')
        else:
            print('    [ERROR] argument is neither a string nor a number')

    ############################################################################
    #   methods
    ############################################################################

    def set_fpath(self):
        # so far we take the same directory as this file is in
        self.base = os.path.dirname(os.path.realpath(__file__))+'/'
        # ToDo: read the path value, so it saved where the raw data is
        self.fpath = self.base+'tomo_center.config'

    def print_fpath(self)
        print('# the current config file for the tomo macro is:')
        print('#     '+self.fpath)

    def datetime_str(self):
        return datetime.datetime.now().strftime("%Y/%m/%d-%H:%M:%S")

    def read_config_file(self):
        self.positions = []

        if not os.path.isfile(self.fpath):
            print('did not find a config file:', self.fpath)
            print('created it')
            self.write_header()
        else:
            with open(self.fpath, 'r') as F:
                lines = F.readlines()
            for i, line in enumerate(lines):
                if not line.startswith('#'):
                    split = line.split()
                    self.positions.append([float(x) for x in split[1:]])

    def get_motor_position(self, motor):
        runCommand('wms '+motor)
        return env.lastMacroResult

    def read_current_positions(self):
        result = [self.datetime_str()]
        for motor in self.motors:
            result.append(self.get_motor_position(motor))
        with open(self.fpath, 'a+') as F:
            F.write(self.line_to_str(result)+'\r\n')
        print(self.get_header())
        print(self.line_to_str(result))

    def get_header(self):
        return '# date-time            '+' '.join([m.ljust(8) for m in self.motors])

    def write_header(self):
        with open(self.fpath, 'a+') as F:
            F.write(self.get_header()+'\r\n')
            F.write('#'*86+'\r\n')
        
    def line_to_str(self, line):
        return line[0] +'    ' + ' '.join([str(round(x, 3)).ljust(8) for x in line[1:]])

    def my_sin(self, r_deg, rx, dtheta, cx):
        return np.sin( (r_deg + dtheta)*np.pi/180. )*rx + cx

    def my_cos(self, r_deg, rx, dtheta, cx):
        return np.cos( (r_deg + dtheta)*np.pi/180. )*rx + cx

    def fit_cos_z(self, z, r_deg):
        # guess rx, dtheta, cx
        p0  = [80, -5, 4000]
        fit = curve_fit(self.my_sin, r_deg, z, p0=p0)
        return fit

    def fit_sin(self, x, r_deg):
        # guess rx, dtheta, cx
        p0  = [80, -5, 4000]
        fit = curve_fit(self.my_sin, r_deg, x, p0=p0)
        return fit

    def fit_cos(self, x, r_deg):
        # guess rx, dtheta, cx
        p0  = [80, -5, 4000]
        fit = curve_fit(self.my_cos, r_deg, x, p0=p0)
        return fit

    def read_xyzr(self):
        x, y, z, r = [], [], [], []
        for line in self.positions:
            x.append(line[0]+line[3])
            y.append(line[1]+line[4])
            z.append(line[2]+line[5])
            r.append(line[6])
        return np.array(x), np.array(y), np.array(z), np.array(r)  

    def analyze(self):
        x, y, z, r = self.read_xyzr()
        self.fitx  = self.fit_sin(x, r)
        self.fity  = self.fit_sin(y, r)
        if self.assume_xz_circle:
            # assuming the movement in the x-z-plane is a circle:
            # the z-movement can be calcualted as a cosine to the sine in x
            # with the same phase offset and the same radius, just a
            # different center, which we calcualte from the first saved position
            z_rx       = self.fitx[0][0]
            z_dtheta   = self.fitx[0][1]-90
            z_cz       = z[0]-z_rx*np.sin((z_dtheta+r[0])*np.pi/180.)
            self.fitz  = np.array([[z_rx,z_dtheta,z_cz]])
        else:
            # the z-movement is an independet sine
            # the movement in the x-z-plane could be an ellipsis
            self.fitz  = self.fit_sin(z, r)

    def plot_fits(self):
        x, y, z, r = self.read_xyzr()
        r_deg_plot = np.linspace(-360,360,400)

        cx, cy, cz = self.fitx[0][-1], self.fity[0][-1], self.fitz[0][-1]
        x0, y0, z0 = self.my_sin(0, *self.fitx[0]), self.my_sin(0, *self.fity[0]), self.my_sin(0, *self.fitz[0])

        plt.figure(figsize=(12,6), facecolor='white')
        plt.suptitle(self.datetime_str()+' - '+self.fpath)

        plt.subplot(2,4,1)
        plt.scatter(x,z)
        plt.plot(self.my_sin(r_deg_plot, *self.fitx[0]), self.my_sin(r_deg_plot, *self.fitz[0]), c='r', alpha=0.5)
        plt.scatter([cx], [cz], c='r')
        plt.plot([cx, x0], [cz, z0], c='r')
        plt.axis('equal')
        plt.ylabel(self.motors[2]+' + '+self.motors[5])
        plt.xlabel(self.motors[0]+' + '+self.motors[3])

        plt.subplot(2,4,2)
        plt.scatter(r,x)
        plt.plot(r_deg_plot, self.my_sin(r_deg_plot, *self.fitx[0]), c='r', alpha=0.5)
        plt.ylabel(self.motors[0]+' + '+self.motors[3])
        plt.xlabel(self.motors[6])

        plt.subplot(2,4,3)
        plt.scatter(r,y)
        plt.plot(r_deg_plot, self.my_sin(r_deg_plot, *self.fity[0]), c='r', alpha=0.5)
        plt.ylabel(self.motors[1]+' + '+self.motors[4])
        plt.xlabel(self.motors[6])

        plt.subplot(2,4,4)
        plt.scatter(r,z)
        plt.plot(r_deg_plot, self.my_sin(r_deg_plot, *self.fitz[0]), c='r', alpha=0.5)
        plt.ylabel(self.motors[2]+' + '+self.motors[5])
        plt.xlabel(self.motors[6])

        plt.subplot(2,4,6)
        plt.scatter(r,x-self.my_sin(r, *self.fitx[0]), c='r')
        plt.ylabel('residuum: '+self.motors[0]+' + '+self.motors[3])
        plt.xlabel(self.motors[6])
        plt.subplot(2,4,7)
        plt.scatter(r,y-self.my_sin(r, *self.fity[0]), c='r')
        plt.ylabel('residuum: '+self.motors[1]+' + '+self.motors[4])
        plt.xlabel(self.motors[6])
        plt.subplot(2,4,8)
        plt.scatter(r,z-self.my_sin(r, *self.fitz[0]), c='r')
        plt.ylabel('residuum: '+self.motors[2]+' + '+self.motors[5])
        plt.xlabel(self.motors[6])
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.show()

    def move_motor(self,motor,position):
        runCommand('umv '+motor+' '+str(position))
        #print('umv '+motor+' '+str(position))

    def move(self):
        sr        = float(self.arg)
        fit_basex = self.my_sin(sr, *self.fitx[0])
        fit_basey = self.my_sin(sr, *self.fity[0])
        fit_basez = self.my_sin(sr, *self.fitz[0])
        
        if self.verbosity>=:2
            print('#'*80)
            print('# tomo rotate to:')
            print('# sr = '+str(sr))
            print('#'*80)
            print('### base')
            print('#     basex = '+str(fit_basex))
            print('#     basey = '+str(fit_basey))
            print('#     basez = '+str(fit_basez))
            print('### scanner')
            print('#     sx = sy = sz = 0')
            print('#'*80)

        self.move_motor('sx', 0.0)
        self.move_motor('sy', 0.0)
        self.move_motor('sz', 0.0)
        if sr>=0:
            self.move_motor('sr', str(sr))
        else:
            self.move_motor('sr', str(sr+360))
        self.move_motor('basex', fit_basex)
        self.move_motor('basey', fit_basey)
        self.move_motor('basez', fit_basez)
