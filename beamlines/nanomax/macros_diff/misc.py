"""
This file contains convenience macros for nanomax, kept in
a separate file so as not to clutter the main beamline file.
"""

import PyTango
from contrast.environment import macro, runCommand
from contrast.motors import Motor

@macro
class M1shift(object):
    """
    Shift the focal plane of the vertically focusing KB
    mirror (M1) by the specified distance (in microns).
    """
    def __init__(self, dist):
        self.dist = dist
    def run(self):
        cmd = 'mvr m1fpitch %f' % (self.dist / -1381.0)
        print("Moving the M1 fine pitch piezo like this:\n%s" % cmd)
        runCommand(cmd)

@macro
class M2shift(object):
    """
    Shift the focal plane of the horizontally focusing KB
    mirror (M2) by the specified distance (in microns).
    """
    def __init__(self, dist):
        self.dist = dist
    def run(self):
        cmd = 'mvr m2fpitch %f' % (self.dist / -857.0)
        print("Moving the M2 fine pitch piezo like this:\n%s" % cmd)
        runCommand(cmd)

@macro
class Table(object):
    """
    Turn on or off the detector table motors.

    table <on / off>
    """
    def __init__(self, arg):
        self.arg = arg
    def run(self):
        for m in Motor.getinstances():
            if 'table_' in m.name:
                print('Turning %s %s' % (self.arg, m.name))
                m.proxy.PowerOn = (self.arg.lower() == 'on')

