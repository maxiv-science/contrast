"""
Provides a Motor subclass for the Npoint LC400 piezo driver, and a
helper class for generating waveforms. Relies on the Tango server
developed at MAX IV (available on request!):

* https://gitlab.maxiv.lu.se/kits-maxiv/lib-maxiv-npoint-lc400
* https://gitlab.maxiv.lu.se/kits-maxiv/dev-maxiv-npoint-lc400
"""

import PyTango
from . import Motor
import math
import json
import numpy as np

class LC400Motor(Motor):
    """
    Single axis on the LC400.
    """

    def __init__(self, device, axis, **kwargs):
        """
        :param device: Path to the underlying Tango device.
        :type device: str
        :param axis: Axis number on the Tango controller
        :param ``**kwargs``: Passed on to the base class constructor
        """
        super(LC400Motor, self).__init__(**kwargs)
        assert axis in (1, 2, 3)
        self.proxy = PyTango.DeviceProxy(device)
        self.proxy.set_source(PyTango.DevSource.DEV)
        self.axis = axis
        self._format = '%.3f'

    @property
    def dial_position(self):
        if self.axis == 1:
            val = self.proxy.axis1_position
        elif self.axis == 2:
            val = self.proxy.axis2_position
        elif self.axis == 3:
            val = self.proxy.axis3_position
        return val

    @dial_position.setter
    def dial_position(self, pos):
        if self.axis == 1:
            self.proxy.axis1_position = pos
        elif self.axis == 2:
            self.proxy.axis2_position = pos
        elif self.axis == 3:
            self.proxy.axis3_position = pos

    def busy(self):
        attribute = 'axis%d_position_on_target' % self.axis
        on_target = self.proxy.read_attribute(attribute).value
        return not on_target

    def stop(self):
        self.proxy.stop_waveform()
        self.proxy.stop_recording()


class LC400Waveform(object):
    """
    Class to generate waveform configs for the LC400 piezo controller.
    It generates a JSON string, that can be send to the LC400 Tango
    Server to configure the waveform.
    """

    # constants
    # 24 µs, internal clock cycle of LC.400
    CLOCKCYCLE= 0.000024
    # maximum number of points in a waveform
    MAXPOINTS = 83333

    def __init__(self, axis, startpoint, endpoint, scanpoints, exposuretime, latencytime, accelerationtime, decelerationtime = None, startvelocity = None, endvelocity = None):
        # waveform parameters
        self.axis = axis
        self.axisname = "axis%i" % axis
        stepsize = (endpoint-startpoint)/(scanpoints-1)
        print("step size: ", stepsize)
        self.startpoint = startpoint
        self.endpoint = endpoint + stepsize
        self.scanpoints = scanpoints # scanpoints is intervals+1
        self.exposuretime = exposuretime
        self.latencytime = latencytime
        self.accelerationtime = accelerationtime
        if decelerationtime is None:
            # deceleration time not set, use acceleration time
            self.decelerationtime = accelerationtime
        else:
            self.decelerationtime = decelerationtime

        # calculate linear velocity
        self.velocity = (self.endpoint - self.startpoint)/ ((self.scanpoints) * (exposuretime+latencytime))
        print(f"velocity: {self.velocity:0.3} microns/s")

        # set start velocity
        if startvelocity is None:
            # start velocity not set, use 0 as start velocity
            self.startvelocity = 0
        else:
            self.startvelocity = startvelocity

        # set end velocity
        if endvelocity is None:
            # end velocity not set, use start velocity
            self.endvelocity = self.startvelocity
        else:
            self.endvelocity = endvelocity

        # TODO check for valid start and end velocities, e.g. startvelocity < velocity

        # calculate total time of line (acceleraton phase + linear regime + deceleration phase)
        self.lineartime = self.scanpoints * (self.exposuretime + self.latencytime)
        self.totaltime = self.accelerationtime + self.lineartime + self.decelerationtime

        # deterimine clock cycle delay of LC.400, 0 means no delay
        self.clockcycledelay = math.ceil(math.floor(self.totaltime/self.CLOCKCYCLE)/self.MAXPOINTS) - 1
        print("clock cycle delay: ", self.clockcycledelay)
        # determine optimal number of points in waveform
        self.effectiveclockcycle = self.CLOCKCYCLE * (self.clockcycledelay+1)
        self.waveformpoints = math.floor(self.totaltime / self.effectiveclockcycle)
        # define start cycle of linear phase.
        # This is the time when the LC 400 creates the trigger to start the pandabox for position recording and triggering of other detectors
        self.linearstartindex = math.ceil(self.accelerationtime/self.effectiveclockcycle)
        print("triggger start index: ", self.linearstartindex)
        # start point of the waveform in absolute coordinates of the scanner
        self.absolutstartposition = self.accelerationphase(0)
        print("start position of line is at:", self.absolutstartposition)
        print("scan points: ", self.scanpoints)

    def accelerationphase(self, t):
        # calculate parameters for trajectory
        a = (self.velocity - self.startvelocity) / self.accelerationtime
        b = 1/self.accelerationtime
        c = (self.velocity - self.startvelocity) / self.accelerationtime
        d = self.startvelocity
        e = self.startpoint - self.startvelocity*self.accelerationtime  - ( 0.5 + 1/(4*np.pi**2) ) * (self.velocity - self.startvelocity)*self.accelerationtime
        # calculate trajectory
        x = a/(4*np.pi**2 * b**2) * np.cos(2*np.pi*b*t) + c/2 * t**2 + d*t + e
        return x

    def linearphase(self, t):
        x = self.startpoint + self.velocity*(t-self.accelerationtime)
        return x

    def decelerationphase(self, t):
        # calculate parameters for trajectory
        T_e = self.accelerationtime+self.lineartime
        a = (self.velocity - self.endvelocity) / self.decelerationtime
        b = 1/self.decelerationtime
        c = (self.velocity - self.endvelocity) / self.decelerationtime
        # d1 and d2 should be equivalent
        d1 = self.velocity + c * T_e
        d2 = self.endvelocity + c*(T_e+self.decelerationtime)
        d = d2
        e = self.endpoint + a / (4 * np.pi**2 * b**2) + 1/2 * c * T_e**2 - d * T_e
        # calculate trajectory
        x = -a/(4*np.pi**2 * b**2) * np.cos(2*np.pi*b*(t-T_e)) - c/2 * t**2 + d*t + e
        return x

    def time(self):
        t = np.arange(0,self.totaltime, step = self.effectiveclockcycle)
        return t

    def waveform(self):
        x = []
        for t in self.time():
            if t < self.accelerationtime:
                x.append(self.accelerationphase(t))
            elif t >= self.accelerationtime and t <= self.accelerationtime+self.lineartime:
                x.append(self.linearphase(t))
            elif t > self.accelerationtime+self.lineartime:
                x.append(self.decelerationphase(t))
            else:
                print("not used: ", t)

        if len(x) > self.MAXPOINTS:
            raise Exception("waveform too long")
        print(f"points in wafeform : {len(x)}")
        # offset whole waveform so it starts at 0.
        # Waveforms in the LC400 are relative motions with respect to the physical start position of the motor
        offset = self.accelerationphase(0)
        res = [i - offset for i in x]
        return res

    def reset_json(self):
        """
        Create three waveform jsons which deconfigure each channel:
           r1, r2, r2 = reset_json()
        """
        js = []
        for ax in ('axis1', 'axis2', 'axis3'):
            data = {}
            data["generator"] = "pointlist2"
            data["version"] = "2.0"
            data["ClockScaling"] = 1+1 # a bug in the LC400 Tango Server substracts 1, se we have to add 1
            data["TotalPoints"] = 1
            data["EndLinePoint"] = 1 # is this needed?
            data["FlyScanAxis"] = int(ax[-1])
            # Trigger on/off indeces
            triggers = {}
            triggers["count"] = 1
            triggers["on"] = [0,]
            triggers["off"] = [0,]
            # function definition of output pins
            # we use pin 9 (Out 4) to create the start trigger
            output_pins = {}
            output_pins["9"] = {"polarity": 0, 
                                "function": 0}
            data[ax] = {"triggers": triggers,
                                   "output_pins": output_pins,
                                   "positions": [0.,]}
            js.append(json.dumps(data))
        return js

    def json(self):
        # create json string for LC400 waveform configuration
        data = {}
        data["generator"] = "pointlist2"
        data["version"] = "2.0"
        data["ClockScaling"] = self.clockcycledelay+1 # a bug in the LC400 Tango Server substracts 1, se we have to add 1
        data["TotalPoints"] = self.waveformpoints
        data["EndLinePoint"] = self.waveformpoints # is this needed?
        data["FlyScanAxis"] = self.axis
        # Trigger on/off indeces
        triggers = {}
        triggers["count"] = 1
        triggers["on"] = [self.linearstartindex]
        triggers["off"] = [self.linearstartindex+1]
        # function definition of output pins
        # we use pin 9 (Out 4) to create teh start trigger
        output_pins = {}
        output_pins["9"] = {"polarity": 0, 
                            "function": 3}

        data[self.axisname] = {"triggers": triggers,
                                "output_pins": output_pins,
                                "positions": self.waveform()}

        return json.dumps(data)