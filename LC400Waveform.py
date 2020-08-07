"""
Class to generate waveforms configs for the LC400 piezo controller.
It generates a JSON string, that can be send to the LC400 Tango Server to configure
the waveform.
"""

import numpy as np
import matplotlib.pyplot as plt 
import math
import json


class LC400Waveform(object):
    # constants
    # 24 µs, internal clock cycle of LC.400
    CLOCKCYCLE= 0.000024
    # maximum number of points in a waveform
    MAXPOINTS = 83333

    def __init__(self, axis, startpoint, endpoint, scanpoints, exposuretime, latencytime, accelerationtime, decelerationtime = None, startvelocity = None, endvelocity = None):
        # waveform parameters
        self.axis = axis
        self.axisname = "axis%i" % axis
        self.startpoint = startpoint
        self.endpoint = endpoint
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
        self.velocity = (self.endpoint - self.startpoint)/ ((self.scanpoints-1) * (exposuretime+latencytime))

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
        # start point of the waveform in absolut coordinates of the scanner
        self.absolutstartposition = self.accelerationphase(0)
        print("start position of line is at :", self.absolutstartposition)
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
        
        # offset whole waveform so it starts at 0.
        # Waveforms in the LC400 are relative motions with respect to the physical start position of the motor
        offset = self.accelerationphase(0)
        res = [i - offset for i in x]
        return res

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
