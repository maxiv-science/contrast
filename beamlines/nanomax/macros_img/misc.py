"""
This file contains convenience macros for nanomax, kept in
a separate file so as not to clutter the main beamline file.
"""

import PyTango
import time
from contrast.environment import env, macro, runCommand, register_shortcut
from contrast.motors import Motor
from contrast.motors.SmaractMotor import SmaractLinearMotor
from contrast.motors.NanosMotor import NanosMotor
from contrast.detectors import Detector

# some handy shortcuts
register_shortcut('wopt', 'wm cs* zp* osa*')
register_shortcut('wgrip', 'wm bx by bz sx sy sz sr gr*')
register_shortcut('wsample', 'wm bx by bz sx sy sz sr')
register_shortcut('wnimis', 'wm bx by bz sx sy sz sr gr* cs* zp* osa* xrf* pixdet* mic screen')

def fastshutter_action(state, name):
    """
    Open (state=False) or close (state=True) the fast shutter,
    by setting BITS1.outb high or low on the panda box with
    the give name.
    """
    try:
        panda = [m for m in Detector.getinstances() if m.name == name][0]
    except IndexError:
        raise Exception('No Gadget named %s' % name)
    response = panda.query('BITS1.B=%u' % (int(state)))
    if 'OK' in response:
        act = {False: 'opened', True: 'closed'}[state]
        print('Fastshutter %s' % act)
    else:
        print('Could not actuate the shutter')

@macro
class FsOpen(object):
    """
    Opens the fast shutter.
    """
    def run(self):
        fastshutter_action(False, 'panda2')

@macro
class FsClose(object):
    """
    Closes the fast shutter.
    """
    def run(self):
        fastshutter_action(True, 'panda2')

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

@macro
class NewSample(object):
    """
    Set the sample directory at the imaging endstation.
    Usage:
        %newsample '0000_setup'

    would set the data directory to:
    /data/visitors/nanomax/<proposalID>/<visit>/raw/0000_setup/

    You can double check it by typing 'path' afterwards to show
    the current directory data is saved in.
    """

    def __init__(self, NewSampleName):
        self.NewSampleName = NewSampleName
        self.sdm_mac = PyTango.DeviceProxy("B303A-E01/CTL/SDM-01")

    def run(self):
        self.sdm_mac.Sample  = self.NewSampleName

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


