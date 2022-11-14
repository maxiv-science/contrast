"""
This file contains convenience macros for nanomax, kept in
a separate file so as not to clutter the main beamline file.
"""

import PyTango
import time
from contrast.environment import env, macro, runCommand
from contrast.motors import Motor
from contrast.motors.SmaractMotor import SmaractLinearMotor
from contrast.motors.NanosMotor import NanosMotor


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
class GripperHoming(object):
    """
    Homing the motors for the sample gripper
    """

    def run(self):
        for m in Motor.getinstances():
            if m.name == 'grx':
                self.grx = m
            elif m.name == 'gry':
                self.gry = m
            elif m.name == 'grz':
                self.grz = m
            elif m.name == 'gripper':
                self.gripper = m
        
        # homing of gripper y position. The homing is against the top hard stop. Note, this stage doesn't have a functioning reference mark. 
        if input('Home gripper y-motion (y/n)?').lower().strip() == 'y':   
            self.gry.position()
            self.gry.proxy.ArbitraryAsk('N8') 
            while self.gry.proxy.ArbitraryAsk('n') != '0':
                print('Searching gry upper hard stop...')
                time.sleep(1)
            print(self.gry.position())

        # homing of gripper z position. The homing is against the top hard stop, then on the reference mark. 
        if input('Home gripper z-motion (y/n)?').lower().strip() == 'y':   
            self.grz.position()
            self.grz.proxy.ArbitraryAsk('N7')
            while self.grz.proxy.ArbitraryAsk('n') != '0':
                print('Searching grz downstream hard stop')
                time.sleep(1)
            print(self.grz.position())

        # homing of gripper tweezer. The homing is against the most closed hard stop. The reference mark is not reachable. 
        if input('Home gripper tweezer (y/n)?').lower().strip() == 'y':   
            self.gripper.position()
            self.gripper.proxy.ArbitraryAsk('N8') 
            while self.gripper.proxy.ArbitraryAsk('n') != '0':
                print('Searching tweezer closed hard stop...')
                time.sleep(1)
            print(self.gripper.position())

        if input('Home gripper x-motion (y/n)?').lower().strip() == 'y':   
            self.grx.proxy.arbitraryCommand('FRM0,1,1000,1')
            time.sleep(10)
            print(self.grx.position())

        #self.grx.move(0)
        #self.gry.move(0)
        #self.grz.move(0)
        #self.gripper.move(0)

@macro
class SamplePickAndReturn(object):
    """
    Test sequence
    """

    def run(self):
        for m in Motor.getinstances():
            if m.name == 'grx':
                self.grx = m
            elif m.name == 'gry':
                self.gry = m
            elif m.name == 'grz':
                self.grz = m
            elif m.name == 'gripper':
                self.gripper = m

        time.sleep(10)
        print('# pick first sample and move')
        runCommand('umv gripper 2500')
        runCommand('wm gr*')
        runCommand('umv gry 2600')
        runCommand('wm gr*')
        runCommand('umv grz 5000')
        runCommand('wm gr*')
        runCommand('umv grx -6600')
        runCommand('wm gr*')
        runCommand('umv grz -6000')
        runCommand('wm gr*')
        runCommand('umv grx -7100')
        runCommand('wm gr*')
        runCommand('umv gripper 1400')
        runCommand('wm gr*')
        runCommand('umv gry 7500')
        runCommand('wm gr*')
        runCommand('umv grz 5000')
        runCommand('wm gr*')
        runCommand('umv grx 60000')
        runCommand('wm gr*')
        
        print('# return sample to tray')
        runCommand('umv gry 7500')
        runCommand('wm gr*')
        runCommand('umv grz 5000')
        runCommand('wm gr*')
        runCommand('umv grx -7100')
        runCommand('wm gr*')
        runCommand('umv grz -6000')
        runCommand('wm gr*')
        runCommand('umv gry 2600')
        runCommand('wm gr*')
        runCommand('umv gripper 2500')
        runCommand('wm gr*')
        runCommand('umv grx -6600')
        runCommand('wm gr*')
        runCommand('umv grz 5000')
        runCommand('wm gr*')
        runCommand('umv grx -60000')
        runCommand('wm gr*')


