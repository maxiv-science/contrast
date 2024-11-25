"""
A macro to move the sample robot to sample postions in the tray and to the scanner.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from contrast.environment import env, macro, register_shortcut, runCommand


@macro
class Robot(object):
    """
    Move the sample robot to pre-defined postions in the sample tray or the scanner
    %robot <action> <argument>
    """

    def __init__(self, *args):
        self.args = args

    def run(self):
        if self.args[0] == 'goto':
            print('move gripper to pos ', self.args[1])


