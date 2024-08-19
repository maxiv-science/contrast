from .Detector import (
    Detector, TriggeredDetector)
# from ..recorders.Hdf5Recorder import Link
from ..environment import env

import time
import numpy as np
import os
import requests
import json
from threading import Thread
from base64 import b64encode, b64decode


VALID_RANGES = {
    "Pico": ["1 nA", "10 nA", "100 nA"],
    "Nano": ["100 nA", "1 uA", "10 uA"],
    "Micro": ["10 uA", "100 uA", "1 mA"]
}
VALID_SAMPLINGS = ["1", "10", "100", "1000", "10000", "100000"]

class Xandy(Detector, TriggeredDetector):
    """
    Provides a direct interface to the CIVIDEX XandY Beamposition Monitor.
    """

    def __init__(self, name=None, host='b-nanomax-user-devices-0.maxiv.lu.se', port=2848,
                 amplification="Micro", range="1 mA", sampling="100",
                 debug = True):
        """
        Class to interact directly with the XandY API.
        """
        self.host = host
        self.port = port
        self.debug = debug
        self._bias = None
        self._amplification = amplification
        self._range = range
        self._sampling = sampling
        self._sleep = 0
        Detector.__init__(self, name=name)
        TriggeredDetector.__init__(self)

    def initialize(self):
        self.session = requests.Session()
        self.session.trust_env = False

    def _get(self, subsystem, value=None, timeout=3.0):
        url = f"http://{self.host}:{self.port}/api/{subsystem}"
        if self.debug:
            print(f"XANDY posting:\n{url = }{value = }")
        response = self.session.post(url, json=value, timeout=timeout)
        if response:
            if 'application/json' in response.headers['content-type']:
                if self.debug:
                    print(f"XANDY reponded:\n{response}\n{response.json()}")
                return response.json()
            else:
                print('unkown response type', response.headers['content-type'])
        else:
            print('error')
            print(response)

    def _set(self, subsystem, value=None, timeout=3.0):
        url = f"http://{self.host}:{self.port}/api/{subsystem}"
        if self.debug:
            print(f"XANDY posting:\n{url = }{value = }")
        response = self.session.post(url, json=value, timeout=timeout)
        if response.status_code != 200:
            print(response.text)

    def busy(self):
        ret = self._get("command", {"cmd": "status"})
        if ret['Running']:
            return True
        else:
            return False

    @property
    def bias(self):
        """ Detector Bias Voltage in V """
        return self._bias

    @bias.setter
    def bias(self, val):
        ret = self._get('command',{"cmd": "set-bias-voltage", "Voltage":int(val)})
        self._bias = int(ret["Bias-Voltage"][:-2]) # [:-2] truncates the " V" from the response
        
    @property
    def amplification(self):
        """ Amplifier settings """
        return self._amplification

    @amplification.setter
    def amplification(self, val):
        if val in VALID_RANGES.keys():
            self._amplification = val
        else:
            raise ValueError(f"{val} is not a valid amplification. Must be in {list(VALID_RANGES.keys())}")
    
    @property
    def range(self):
        """ Range settings """
        return self._range

    @range.setter
    def range(self, val):
        if val in VALID_RANGES[self._amplification]:
            self._range = val
        else:
            raise ValueError(f"{val} is not a valid range. Must be in {list(VALID_RANGES[self._amplification])}")

    @property
    def sampling(self):
        """ Sampling settings """
        return self._sampling

    @sampling.setter
    def sampling(self, val):
        if str(val) in VALID_SAMPLINGS:
            self._sampling = str(val)
        else:
            raise ValueError(f"{val} is not a valid sampling setting. Must be in {VALID_SAMPLINGS}")
    
    def prepare(self, acqtime, dataid, n_starts):
        self._acqtime = acqtime
        self.n_started = 0
        # stop any acquisitions that may have been started in the GUI
        self.stop()

    def arm(self):
        # if software triggered, we do not arm the xandy
        # if hw triggered, arm xandy
        if self.hw_trig:
            trigger_level = "2000" # definition of TTL high
            config = {
                "cmd": "start",
                "Range": self.range,
                "Amplifier": self.amplification,
                "Hz": self.sampling,
                "ext-Trigger": trigger_level,
                "DAC-1": "x-Position",
                "DAC-2": "y-Position",
                "Record-length": f"{self._acqtime}"
            }
            self._set("command", config)
            time.sleep(self._sleep)

    def start(self):
        # if software triggered, we start the xandy at each point
        self.n_started += 1
        if not self.hw_trig:
            trigger_level = "0"
            config = {
                "cmd": "start",
                "Range": self.range,
                "Amplifier": self.amplification,
                "Hz": self.sampling,
                "ext-Trigger": trigger_level,
                "DAC-1": "x-Position",
                "DAC-2": "y-Position",
                "Record-length": f"{self._acqtime}"
            }
            self._set("command", config)

    def stop(self):
        self._set('command',{'cmd':'stop'})

    def read(self):
        url = f"http://{self.host}:{self.port}/api/data"
        data = self.session.get(url).json()
        if self.debug:
            print(f"XAND returned data:\n{data}")
            
        # convert response to numpy arrays    
        keys = data.keys()
        ret = {}
        n_points = int(self._acqtime*int(self._sampling))
        for k in keys:
            values = np.array(data[k])
            if len(values)!=n_points:
                print(f"xandy got not the correcnt number of points: {np.shape(values) = }, expected {n_points}")
            values = values[0:n_points].reshape((1,-1))
            ret[k] = values
        if self.debug:
            print(f"sending to recorders:\n{ret}")
        # print(ret)
        return ret
    
    def offset_correction(self):
        """ perform an offset correction """
        print("Detector must not be exposed to X-rays when an offset correction is performed.")
        self._set('command',{'cmd':'offset-correction'})
        
    def pid_start(self):
        """ start the PID loop"""
        self._set("pid",{"on/off": 1})
        
    def pid_stop(self):
        """ stop the PID loop"""
        self._set("pid",{"on/off": 0})
 
    @property
    def pid_settings_x(self):
        """ read settings for X PID loop """ 
        ret = self._get("pid", {})
        return (ret["p_x"], ret["i_x"], ret["d_x"])
        
    @pid_settings_x.setter
    def pid_settings_x(self, val):
        p = val[0]
        i = val[1]
        d = val[2]
        self._set("pid", {"p_x": p ,"i_x":i , "d_x":d})
        
    @property
    def pid_settings_y(self):
        """ read settings for Y PID loop """ 
        ret = self._get("pid", {})
        return (ret["p_y"], ret["i_y"], ret["d_y"])
        
    @pid_settings_y.setter
    def pid_settings_y(self, val):
        p = val[0]
        i = val[1]
        d = val[2]
        self._set("pid", {"p_y": p ,"i_y":i , "d_y":d})
        
    @property
    def pid_voltage_x(self):
        """ read X voltage output in mV"""
        ret = self._get("pid", {})
        return ret["voltage_x"]
    
    @pid_voltage_x.setter
    def pid_voltage_x(self, val):
        """ set X voltage in mV"""
        self._set("pid", {"voltage_x": val})
        
    @property
    def pid_voltage_y(self):
        """ read Y voltage output in mV"""
        ret = self._get("pid", {})
        return ret["voltage_y"]
    
    @pid_voltage_y.setter
    def pid_voltage_y(self, val):
        """ set Y voltage in mV"""
        self._set("pid", {"voltage_y": val})
        
    @property
    def pid_x_target(self):
        """ read relative X target position"""
        ret = self._get("pid", {})
        return ret["x-target"]
    
    @pid_x_target.setter
    def pid_x_target(self, val):
        """ set relative X target position"""
        self._set("pid", {"x-target": val})

    @property
    def pid_y_target(self):
        """ read relative Y target position"""
        ret = self._get("pid", {})
        return ret["y-target"]
    
    @pid_y_target.setter
    def pid_y_target(self, val):
        """ set relative Y target position"""
        self._set("pid", {"y-target": val})      