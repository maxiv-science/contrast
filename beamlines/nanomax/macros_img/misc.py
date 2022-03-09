"""
This file contains convenience macros for nanomax, kept in
a separate file so as not to clutter the main beamline file.
"""

import PyTango
import time
from contrast.environment import macro, runCommand


@macro
class ShOpen(object):
    """
    Open the beamline shutter in optics hutch 2
    """

    def run(self):
        proxy = PyTango.DeviceProxy('tango://B303A-O/PSS/BS-01')
        proxy.Open()
        for x in range(10):
            time.sleep(0.5)
            if proxy.State() == PyTango.DevState.OPEN:
                print('Shutter is open')
                return
        print('Shutter could not be opened! Is the hutch searched?')

@macro
class ShClose(object):
    """
    Close the beamline shutter in optics hutch 2
    """

    def run(self):
        proxy = PyTango.DeviceProxy('tango://B303A-O/PSS/BS-01')
        proxy.Close()
        for x in range(10):
            time.sleep(0.5)
            if proxy.State() == PyTango.DevState.CLOSE:
                print('Shutter is closed')
                return
        print('Shutter could not be closed!')



