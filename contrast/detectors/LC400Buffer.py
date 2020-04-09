from .Detector import Detector

import time
import numpy as np
import PyTango

class LC400Buffer(Detector):
    """
    Class representing the LC400 piezo machine under the
    control of the LC400ScanControl Tango device, used for
    reading the flyscan positions.
    """

    def __init__(self, name=None, device=None, xaxis=2, yaxis=3, zaxis=1):
        self.proxy = PyTango.DeviceProxy(device)
        Detector.__init__(self, name=name)
        self.xaxis = xaxis
        self.yaxis = yaxis
        self.zaxis = zaxis

    def initialize(self):
        self.proxy.init()

    def stop(self):
        self.proxy.Stop()

    def busy(self):
        return not (self.proxy.State() in (PyTango.DevState.STANDBY, PyTango.DevState.ON))

    def __emergency_backup(self):
        # grab these values in case we have to restart and reset
        grab_keys = ("FlyScanMotorStartPosition", "FlyScanMotorEndPosition", "NumberOfIntervals", 
                     "GateWidth", "GateLatency", "FlyScanMotorAxis")
        self.sc_params = {k:self.proxy.read_attribute(k).value for k in grab_keys}

    def __emergency_recover(self):
        ec0 = PyTango.DeviceProxy('tango/admin/b-v-nanomax-ec-0')
        ioc = PyTango.DeviceProxy('tango/admin/b-nanomax-ec-6')
        ec0.HardKillServer('LC400ScanControl/B303A')
        ioc.HardKillServer('NpointLC400/B303A')
        print('Killing the npoint devices and waiting...')
        for i in range(10):
            print('*')
            time.sleep(1)
        ioc.DevStart('NpointLC400/B303A')
        print('Starting the npoint motor device and waiting...')
        for i in range(10):
            print('*')
            time.sleep(1)
        ec0.DevStart('LC400ScanControl/B303A')
        print('Starting the npoint scancontrol device and waiting...')
        for i in range(10):
            print('*')
            time.sleep(1)
        self.initialize()
        for k, v in self.sc_params.items():
            self.proxy.write_attribute(k, v)
        self.proxy.ConfigureLC400Motion()
        self.proxy.ConfigureLC400Recorder()
        self.proxy.ConfigureStanford()

    def read(self):
        self.__emergency_backup()
        try:
            self.proxy.ReadLC400Buffer()
            data = {1: self.proxy.Axis1Positions,
                    2: self.proxy.Axis2Positions,
                    3: self.proxy.Axis3Positions,}
            self.length = len(data[1])
        except PyTango.DevFailed:
            self.__emergency_recover()
            fake = np.ones(self.length, dtype=np.float) * -1
            data = {i: fake for i in (1,2,3)}
        return {'x': data[self.xaxis], 'y': data[self.yaxis], 'z': data[self.zaxis]}

    def start(self):
        """
        Placeholder, this detector just reads out whatever buffer is on the
        scancontrol device. That device is managed manually from macros.
        """
        pass

