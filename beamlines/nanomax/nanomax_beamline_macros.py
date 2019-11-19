"""
This file contains convenience macros for nanomax, kept in
a separate file so as not to clutter the main beamline file.
"""

import PyTango
from contrast.environment import macro, register_shortcut, runCommand

# some handy shortcuts
register_shortcut('diode1in', 'mv diode1_x 0')
register_shortcut('diode1out', 'mv diode1_x -40000')
register_shortcut('diode2in', 'mv diode2_y 30000')
register_shortcut('diode2out', 'mv diode2_y 0')
register_shortcut('fsin', 'mv fastshutter_x 0')
register_shortcut('fsout', 'mv fastshutter_x -26000')
register_shortcut('watten', 'wm attenuator*')
register_shortcut('wsample', 'wm base* s?')
register_shortcut('wbl', 'wm ivu_* energy ssa_gap*')

@macro
class FsOpen(object):
    """
    Opens the fast shutter.
    """
    def run(self):
        fastshutter = PyTango.DeviceProxy("B303A-A100380/CTL/ADLINKDIO-01")
        try:
            fastshutter.write_attribute("Shutter",False)
            print("Fastshutter is now opened")
        except:
            print("Fastshutter could not be opened")
        # Workaround: as long as the fast shutter is at the wrong height,
        # use one of the slit blades in DM4 instead
        print("Moving seh_top blade out")
        runCommand('umv seh_top 3000')

@macro
class FsClose(object):
    """
    Closes the fast shutter.
    """
    def run(self):
        fastshutter = PyTango.DeviceProxy("B303A-A100380/CTL/ADLINKDIO-01")
        try:
            fastshutter.write_attribute("Shutter",True)
            print("Fastshutter is now closed")
        except:
            print("Fastshutter could not be closed")
        # Workaround: as long as the fast shutter is at the wrong height,
        # use one of the slit blades in DM4 instead
        print("Moving seh_top blade in")
        runCommand('umv seh_top 0')


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

