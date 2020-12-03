"""
This file contains convenience macros for nanomax, kept in
a separate file so as not to clutter the main beamline file.
"""

import PyTango
from contrast.environment import macro, register_shortcut, runCommand

# some handy shortcuts
register_shortcut('diode1in', 'umv diode1_x 40000')
register_shortcut('diode1out', 'umv diode1_x 0')
register_shortcut('diode2in', 'umv diode2_y 30000')
register_shortcut('diode2out', 'umv diode2_y 0')
register_shortcut('fsin', 'umv fastshutter_x 25800')
register_shortcut('fsout', 'umv fastshutter_x 0')
register_shortcut('watten', 'wm attenuator*')
register_shortcut('wsample', 'wm base* s?')
register_shortcut('wbl', 'wm ivu_* energy mono_x2per ssa_gap*')

@macro
class FsOpen(object):
    """
    Opens the fast shutter.
    """
    def run(self):
        #fastshutter = PyTango.DeviceProxy("B303A-A100380/CTL/ADLINKDIO-01")
        try:
            #fastshutter.write_attribute("Shutter",False)
            #decive is B303A-EH/CTL/PZCU-04B303A-EH/CTL/PZCU-04
            runCommand('umv seh_left 1000')
            print("Fastshutter is now opened")
        except:
            print("Fastshutter could not be opened")

@macro
class FsClose(object):
    """
    Closes the fast shutter.
    """
    def run(self):
        #fastshutter = PyTango.DeviceProxy("B303A-A100380/CTL/ADLINKDIO-01")
        try:
            #fastshutter.write_attribute("Shutter",True)
            runCommand('umv seh_left -4000')
            print("Fastshutter is now closed")
        except:
            print("Fastshutter could not be closed")

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

