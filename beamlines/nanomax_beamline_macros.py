"""
This file contains convenience macros for nanomax, kept in
a separate file so as not to clutter the main beamline file.
"""

import PyTango
from contrast.environment import macro, register_shortcut

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

