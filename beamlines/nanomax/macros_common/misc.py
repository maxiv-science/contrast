"""
This file contains convenience macros for nanomax, kept in
a separate file so as not to clutter the main beamline file.
"""

import PyTango
from contrast.environment import macro, register_shortcut
from contrast.detectors import Detector
from contrast.motors import Motor

# some handy shortcuts
register_shortcut('diode1in', 'umv diode1_x 18000')
register_shortcut('diode1out', 'umv diode1_x -18000')
register_shortcut('diode2in', 'umv diode2_y 15000')
register_shortcut('diode2out', 'umv diode2_y -15000')
register_shortcut('fsin', 'umv fastshutter_y -11600')
register_shortcut('fsout', 'umv fastshutter_y 14000')
register_shortcut('watten', 'wm attenuator*')
register_shortcut('wbl', 'wm ivu_* energy mono_x2per ssa_gap*')


@macro
class Optics(object):
    """
    Turn the optics motors on, off, or see their state.

    optics <on / off>
    optics  - prints status
    """
    def __init__(self, arg=None):
        self.arg = arg

        self.green = '\033[92m'
        self.yellow = '\033[93m'
        self.red = '\033[91m'
        self.bold = '\033[1m'
        self.end = '\033[0m'

    def run(self):
        if self.arg is None:
            self.print_all_motors_states()
        else:
            self.check_and_set_all_motors()
            self.print_all_motors_states()
    
    def is_optics_motor(self, m):
        """
        returns True if the given motor is part of the ones
        to be checked
        """
        return ('hfm_' in m.name
                or 'vfm_' in m.name
                or ('mono_' in m.name and not 'f' in m.name))

    def print_all_motors_states(self):
        """
        just prints the states of all optics motors
        """
        for m in Motor.getinstances():
            if self.is_optics_motor(m):
                self.print_motor_state(m)

    def print_motor_state(self, m):
        """
        prints the current state of a given motor
        """
        if m.proxy.PowerOn:
            print(f'{self.green}{self.bold}(on){self.end} {m.name}')
        else:
            print(f'{self.red}{self.bold}(off){self.end}  {m.name}')

    def check_and_set_all_motors(self):
        """
        sets all motots as requested if not already in that state
        """
        for m in Motor.getinstances():
            if self.is_optics_motor(m):
                self.check_and_set_motor(m)
    def check_and_set_motor(self, m):
        """
        Checks status of the motor.
        If the current state differs from the desired state (self.arg),
        will try to change it. If that fails, an error will be printed. 
        """

        # get requested and state
        current_state = m.proxy.PowerOn
        requested_state = (self.arg.lower() == 'on')

        # do not do anything if requested state matched current state
        if current_state == requested_state:
            print(f'{m.name} is already {self.arg.lower()}')

        # change states if needed
        if current_state != requested_state:
            print(f'Turning {self.arg} {m.name}')
            m.proxy.PowerOn = requested_state

            # check if the changing of states worked
            current_state = m.proxy.PowerOn
            if current_state != requested_state:
                print(f'{self.yellow}{self.bold}failed to turn {self.arg} {m.name}{self.end}')


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


