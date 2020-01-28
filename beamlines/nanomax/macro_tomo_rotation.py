"""
Lorem Ipsum Dolor Sit Amen
"""

import numpy as np
from contrast.environment import env, macro, register_shortcut, runCommand

@macro
class tomo_rotation(object):
    """
    Lorem Ipsum Dolor Sit Amen
    """

    def __init__(self, angle_deg):
        self.angle_deg        = angle_deg
        self.basex_c          = -5432.96
        self.basez_c          =  -824.40
        self.r                =   142.8
        self.angle_deg_offset =   -33.0
        
    def get_motor_position(self, motor):
        runCommand('wms '+motor)
        return env.lastMacroResult

    def move_motor_to(self, motor, pos):
        runCommand('mv '+motor+' '+str(pos))
        pass

    def rotate(self):
        self.move_motor_to('sr', self.angle_deg*160)

    def compensate_base(self):
        angle_rad = (-self.angle_deg+self.angle_deg_offset)*np.pi/180.
        basex     = self.basex_c + np.sin(angle_rad)*self.r
        basez     = self.basez_c + np.cos(angle_rad)*self.r
        self.move_motor_to('basex', basex)
        self.move_motor_to('basez', basez)
        print(str(basex)[:8], str(basez)[:8])

    def run(self):

        # rotate
        self.rotate()

        # compensate with the base
        self.compensate_base()

