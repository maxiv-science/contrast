"""
This file contains convenience macros for nanomax diffraction station, kept in
a separate file so as not to clutter the main beamline file.
"""

import PyTango
import time
from contrast.environment import macro, runCommand, register_shortcut
from contrast.motors import Motor
from contrast.detectors import Detector

# some handy shortcuts
register_shortcut('wtab', 'wm table*')
register_shortcut('wrobot', 'wm gamma delta radius')
register_shortcut('wsample', 'wm base* s?')


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
class Scanner(object):
    """
    Turn the scanner motors on, off, or see their state.

    scanner <on / off>
    scanner  - prints status
    """
    def __init__(self, arg=None):
        self.arg = arg

    def run(self):
        for m in Motor.getinstances():
            if ('sx' == m.name):
                if self.arg is None:
                    pass
                    #print(f"({{True:'on', False:'OFF'}[m.proxy.axis1_pid_enable]}) axis1")
                    #print(f"({{True:'on', False:'OFF'}[m.proxy.axis2_pid_enable]}) axis2")
                    #print(f"({{True:'on', False:'OFF'}[m.proxy.axis3_pid_enable]}) axis3")
                else:
                    print(f'Turning scanner {self.arg.lower()}')
                    state = (self.arg.lower() == 'on')
                    m.proxy.axis1_pid_enable = state
                    m.proxy.axis2_pid_enable = state
                    m.proxy.axis3_pid_enable = state

@macro
class FsOpen(object):
    """
    Opens the fast shutter.
    """
    def run(self):
        # fastshutter_action(False, 'panda0')
        runCommand('umv seh_left 2000')

@macro
class FsClose(object):
    """
    Closes the fast shutter.
    """
    def run(self):
        # fastshutter_action(True, 'panda0')
        runCommand('umv seh_left -2000')

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

@macro
class ShOpen(object):
    """
    Open the beamline shutter in experimental hutch 1
    """

    def run(self):
        proxy = PyTango.DeviceProxy('tango://B303A-E/PSS/BS-01')
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
    Close the beamline shutter in experimental hutch 1
    """

    def run(self):
        proxy = PyTango.DeviceProxy('tango://B303A-E/PSS/BS-01')
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
    Set the sample directory at the diffraction endstation.
    Usage:
        %newsample '0000_setup'

    would set the data directory to:
    /data/visitors/nanomax/<proposalID>/<visit>/raw/0000_setup/

    You can double check it by typing 'path' afterwards to show
    the current directory data is saved in.
    """

    def __init__(self, NewSampleName):
        self.NewSampleName = NewSampleName
        self.sdm_mac = PyTango.DeviceProxy("B303A-E02/CTL/SDM-01")

    def run(self):
        self.sdm_mac.Sample  = self.NewSampleName
