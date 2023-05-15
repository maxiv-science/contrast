"""
Provides a ``Motor`` subclass for Nanos positioners.
"""

import PyTango
import time
from . import Motor


class NanosMotor(Motor):
    """
    Single Nanos motor axis.
    """

    def __init__(self, device, axis, velocity=500, **kwargs):
        """
        :param device: Path to the Bmc101 Tango device
        :type device: str
        :param axis: Axis number on the controller
        :type axis: int
        :param ``**kwargs``: Passed on to the ``Motor`` base class
        """
        super(NanosMotor, self).__init__(**kwargs)
        self.proxy = PyTango.DeviceProxy(device)
        self.proxy.set_source(PyTango.DevSource.DEV)
        self._axis = int(axis)
        if self.proxy.State() == PyTango.DevState.STANDBY:
            self.proxy.Connect()
        ax = '#%02d\r' % self._axis
        self.proxy.ArbitrarySend(ax)
        val = 'Y8=%d' % velocity
        self.proxy.ArbitraryAsk(val)

    @property
    def dial_position(self):
        attr = 'channel%02d_encoder' % self._axis
        return self.proxy.read_attribute(attr).value

    @dial_position.setter
    def dial_position(self, pos):
        attr = 'channel%02d_position' % self._axis
        self.proxy.write_attribute(attr, pos)

    def busy(self):
        attr = 'channel%02d_state' % self._axis
        return not (self.proxy.read_attribute(attr).value == 'STATIONARY')

    def stop(self):
        self.proxy.StopAll()  # safety first

    def reset_encoder(self):
        # Sets the encoder position to zero
        ax = '#%02d\r' % self._axis
        self.proxy.ArbitrarySend(ax)
        time.sleep(0.1)
        self.proxy.ArbitrarySend('O0\r')

    def home(self):
        #print('Homeing is currently not safe to execute. No action right now.')

        ax = '#%02d\r' % self._axis
        self.proxy.ArbitrarySend(ax)
        time.sleep(0.1)
        self.proxy.ArbitrarySend('N9\r')
        ret = ''
        while(ret != '0'):
            ret = self.proxy.ArbitraryAsk('n')
            mess = 'Homing axis %d status=%s' % (self._axis, ret)
            print(mess)
            time.sleep(2)
        print('Homing finished')

