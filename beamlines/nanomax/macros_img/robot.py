"""
A macro to move the sample robot to sample postions in the tray and to the scanner.
"""

import os
import time
import numpy as np
import matplotlib.pyplot as plt
from contrast.environment import env, macro, register_shortcut, runCommand
from contrast.motors import Motor
from math import isclose

@macro
class Robot(object):
    """
    Move the sample robot to pre-defined postions in the sample tray or the scanner
    %robot <action> <argument>
    """

    def __init__(self, *args):
        self.args = args
        self.print_only = False
        self.tray_ref_pos = (7571, -5394, 943, -2406) # motor positions, grx, gry, grz, grip, for sample in tray position BP3
        self.grip_open_gap = 2000
        tray_spacing = (5700, 8000, 7000)
        self.sample_positions = {
            'BP3':(self.tray_ref_pos[0] - 0 * tray_spacing[0], self.tray_ref_pos[1], self.tray_ref_pos[2]),
            'BP2':(self.tray_ref_pos[0] - 1 * tray_spacing[0], self.tray_ref_pos[1], self.tray_ref_pos[2]),
            'BP1':(self.tray_ref_pos[0] - 2 * tray_spacing[0], self.tray_ref_pos[1], self.tray_ref_pos[2]),
            'B1':(self.tray_ref_pos[0] - 3 * tray_spacing[0], self.tray_ref_pos[1], self.tray_ref_pos[2]),
            'B2':(self.tray_ref_pos[0] - 4 * tray_spacing[0], self.tray_ref_pos[1], self.tray_ref_pos[2]),
            'B3':(self.tray_ref_pos[0] - 5 * tray_spacing[0], self.tray_ref_pos[1], self.tray_ref_pos[2]),
            'B4':(self.tray_ref_pos[0] - 6 * tray_spacing[0], self.tray_ref_pos[1], self.tray_ref_pos[2]),
            'B5':(self.tray_ref_pos[0] - 7 * tray_spacing[0], self.tray_ref_pos[1], self.tray_ref_pos[2]),
            'B6':(self.tray_ref_pos[0] - 8 * tray_spacing[0], self.tray_ref_pos[1], self.tray_ref_pos[2]),
            'B7':(self.tray_ref_pos[0] - 9 * tray_spacing[0], self.tray_ref_pos[1], self.tray_ref_pos[2]),
            'B8':(self.tray_ref_pos[0] - 10 * tray_spacing[0], self.tray_ref_pos[1], self.tray_ref_pos[2]),
            'B9':(self.tray_ref_pos[0] - 11 * tray_spacing[0], self.tray_ref_pos[1], self.tray_ref_pos[2]),
            'B10':(self.tray_ref_pos[0] - 12 * tray_spacing[0], self.tray_ref_pos[1], self.tray_ref_pos[2]),
            'TP3':(self.tray_ref_pos[0] - 0 * tray_spacing[0], self.tray_ref_pos[1] + tray_spacing[1], self.tray_ref_pos[2] - tray_spacing[2]),
            'TP2':(self.tray_ref_pos[0] - 1 * tray_spacing[0], self.tray_ref_pos[1] + tray_spacing[1], self.tray_ref_pos[2] - tray_spacing[2]),
            'TP1':(self.tray_ref_pos[0] - 2 * tray_spacing[0], self.tray_ref_pos[1] + tray_spacing[1], self.tray_ref_pos[2] - tray_spacing[2]),
            'T1':(self.tray_ref_pos[0] - 3 * tray_spacing[0], self.tray_ref_pos[1] + tray_spacing[1], self.tray_ref_pos[2] - tray_spacing[2]),
            'T2':(self.tray_ref_pos[0] - 4 * tray_spacing[0], self.tray_ref_pos[1] + tray_spacing[1], self.tray_ref_pos[2] - tray_spacing[2]),
            'T3':(self.tray_ref_pos[0] - 5 * tray_spacing[0], self.tray_ref_pos[1] + tray_spacing[1], self.tray_ref_pos[2] - tray_spacing[2]),
            'T4':(self.tray_ref_pos[0] - 6 * tray_spacing[0], self.tray_ref_pos[1] + tray_spacing[1], self.tray_ref_pos[2] - tray_spacing[2]),
            'T5':(self.tray_ref_pos[0] - 7 * tray_spacing[0], self.tray_ref_pos[1] + tray_spacing[1], self.tray_ref_pos[2] - tray_spacing[2]),
            'T6':(self.tray_ref_pos[0] - 8 * tray_spacing[0], self.tray_ref_pos[1] + tray_spacing[1], self.tray_ref_pos[2] - tray_spacing[2]),
            'T7':(self.tray_ref_pos[0] - 9 * tray_spacing[0], self.tray_ref_pos[1] + tray_spacing[1], self.tray_ref_pos[2] - tray_spacing[2]),
            'T8':(self.tray_ref_pos[0] - 10 * tray_spacing[0], self.tray_ref_pos[1] + tray_spacing[1], self.tray_ref_pos[2] - tray_spacing[2]),
            'T9':(self.tray_ref_pos[0] - 11 * tray_spacing[0], self.tray_ref_pos[1] + tray_spacing[1], self.tray_ref_pos[2] - tray_spacing[2]),
            'T10':(self.tray_ref_pos[0] - 12 * tray_spacing[0], self.tray_ref_pos[1] + tray_spacing[1], self.tray_ref_pos[2] - tray_spacing[2])
        }
        for m in Motor.getinstances():
            if m.name in 'grx':
                self.grx = m
            if m.name in 'gry':
                self.gry = m
            if m.name in 'grz':
                self.grz = m
            if m.name in 'grip':
                self.grip = m

    def run(self):
        print('The sample robot, the gripper, macro is under development. It is not safe to operate it. Therefore all actions are disabled')
            return
            
        if not self._is_robot_homed():
            return

        if self.args[0] == 'goto':
            self._action_goto(self.args[1])

        elif self.args[0] == 'release':
            self._action_open()

        elif self.args[0] == 'hold':
            self._action_close()

        elif self.args[0] == 'lift':
            print('lift sample out of mirror or tray')

        elif self.args[0] == 'drop':
            print('drop sample into mirror or tray')

        else:
            print('unknown action for the robot')

    def _action_goto(self, sample):
            sample_name = sample.upper()
            sample_pos = self.sample_positions[sample_name]
            print('move gripper to pos', sample_name, sample_pos)
            if self._is_grip_close():
                self._move_robot_xyz('y', 8000)
                self._move_robot_xyz('z', 8000)
                self._move_robot_xyz('x', sample_pos[0])
                self._move_robot_xyz('z', sample_pos[2])
                self._move_robot_xyz('y', sample_pos[1])
            if self._is_grip_open():
                self._move_robot_xyz('z', 8000)
                self._move_robot_xyz('y', 8000)
                self._move_robot_xyz('x', sample_pos[0])
                self._move_robot_xyz('y', sample_pos[1])
                self._move_robot_xyz('z', sample_pos[2])

    def _action_open(self):
        if self._is_grip_close():
            new_pos_grip = self.tray_ref_pos[3] + self.grip_open_gap
            curr_pos_grx = self.grx.dial_position
            new_pos_grx = curr_pos_grx + self.grip_open_gap / 2
            self.grip.dial_position = new_pos_grip
            self.grx.dial_position = new_pos_grx

    def _action_close(self):
        if self._is_grip_open():
            new_pos_grip = self.tray_ref_pos[3]
            curr_pos_grx = self.grx.dial_position
            new_pos_grx = curr_pos_grx - self.grip_open_gap / 2
            self.grx.dial_position = new_pos_grx
            self.grip.dial_position = new_pos_grip

    def _action_lift(self):
        pass

    def _action_drop(self):
        pass

    def _is_grip_open(self):
        return isclose(self.grip.dial_position, self.tray_ref_pos[3] + self.grip_open_gap, abs_tol = 100)

    def _is_grip_close(self):
        return isclose(self.grip.dial_position, self.tray_ref_pos[3], abs_tol = 100)

    def _is_robot_homed(self):
        grx_homed = False
        gry_homed = False
        grz_homed = False
        grip_homed = False
        status = self.grx.proxy.read_attribute(f'status_{self.grx.axis}').value
        if status.find('IS_REFERENCED : True') > -1:
            grx_homed = True
        status = self.gry.proxy.read_attribute(f'status_{self.gry.axis}').value
        if status.find('IS_REFERENCED : True') > -1:
            gry_homed = True
        status = self.grz.proxy.read_attribute(f'status_{self.grz.axis}').value
        if status.find('IS_REFERENCED : True') > -1:
            grz_homed = True
        status = self.grip.proxy.read_attribute(f'status_{self.grip.axis}').value
        if status.find('IS_REFERENCED : True') > -1:
            grip_homed = True
        if(grx_homed & gry_homed & grz_homed & grip_homed):
            return True
        else:
            print(f'\033[91m[!]\033[0m Some of the robot motors are not referenced. All motors must be homed to allow the robot to move samples')
            return False

    def _move_robot_xyz(self, axis, pos):
        if(self.print_only):
            print(f'Moving motor {axis} to position {pos}')
            return

        if not self._is_grip_close() and not self._is_grip_open():
            print(f'\033[91m[!]\033[0m The gripper is in an undefined state. It should be either open or close. The robot motion is aborted')
            return

        if axis == 'x':
            if self._is_grip_close():
                self.grx.dial_position = pos             
            elif self._is_grip_open():
                self.grx.dial_position = pos + self.grip_open_gap / 2           
            while self.grx.busy():
                time.sleep(0.1)
        elif axis == 'y':
            self.gry.dial_position = pos             
            while self.gry.busy():
                time.sleep(0.1)
        elif axis == 'z':
            self.grz.dial_position = pos    
            while self.grz.busy():
                time.sleep(0.1)

