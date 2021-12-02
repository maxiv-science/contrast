"""
Softimamax class for Panda that adds Softimax specific functionality

This class assumes that:
1) the PCAP block is used
2) the number of expected captured data points is provided via burst_n, e.g. panda.burst_n = 43
3) flickering the "A" bit causes a trigger.

"""
from .PandaBox import PandaBox, SOCK_RECV
from .Detector import Detector
from typing import List
import math, time
import tango
import numpy as np

class PandaBoxSofti(PandaBox):
    
    def __init__(self, name=None, host='b-softimax-panda-0.maxiv.lu.se',
                 ctrl_port=8888, data_port=8889):
        """
        The class inherits the PandABox and adds a few Softimax specific features.
        """
        super().__init__(name=name, host=host, ctrl_port=ctrl_port, data_port=data_port)

    def send_table(self, table: List, seq_N=1):
        """
        Sends a table to SEQ block that should be shaped as a list of int values, each 4 consequtive elements will convert into a single table row
        e.g. table = [1507329, 21000, 5, 5, 6815745, 3500, 5, 5] wil convert into two rows with certain repeats, trigger, position, time, and output values
        seq_N is the SEQ block number, currently can be either 1 or 2
        """
        self.ctrl_sock.sendall(bytes(f'SEQ{seq_N}.TABLE<\n', 'ascii'))
        for element in table:
            self.ctrl_sock.sendall(bytes(str(element) + '\n', 'ascii'))
        self.ctrl_sock.sendall(bytes('\n', 'ascii'))
        return self.ctrl_sock.recv(SOCK_RECV).decode()
    
    def _seq1_prepare(self, forward_start, backward_start):
        """
        This function prepares the SEQ1 block, which is needed for the bi-directional scanning
        forward_start, backward_start: the values in µm where the forward and backward lines should start
        """
        backward_start = int(backward_start*1000)
        forward_start = int(forward_start*1000)
        table = [1507329, backward_start, 5, 5, 6815745, forward_start, 5, 5]
        resp = self.send_table(table)
        if resp == 'OK':
            return True
        else:
            return False

    def _pcomp_prepare(self, pre_start, start, stop, N_intervals, forward=True, width_coef = 1):
        '''
        This function is used to prepare the Panda PCOMP blocks according to the needed scan paprameters.
        The pre_start, start, and stop values are in microns.
        The forward and backward parts are set up by the respective PCOMP modules and the forward parameter is used to 
        indicate(choose) the PCOMP module that is going to be prepared.
        width_coef: 1 is for max possible dwell time, i.e. the time when the counters used for STXM are gated.
        '''
        pre_start *= 1000
        start *= 1000
        stop *= 1000
        
        if (start > stop) and forward:
            print("pcomp_prepare warning: Start value should be more negative than stop value for forward scan. Auto swtiched to backward scan preparation.")
            forward = False
        elif (start < stop) and not forward:
            print("pcomp_prepare warning: Start value should be more positive than stop value for backward scan. Auto swtiched to forward scan preparation.")
            forward = True
        # Calculating the step size for PCAP
        step = int(abs(math.ceil((stop-start)/N_intervals)))
        # Checking the step size, it cannot be smaller than two
        if step <= 2:
            raise Exception("PCOMP step cannot be smaller than two, currently: %d" % step)
        # Calculating the width for PCAP
        width = int((step - 1)*width_coef)
        # Checking the width, it cannot be smaller than one
        if width <= 1:
            raise Exception("PCOMP width cannot be smaller than one, currently: %d" % width)
        # Calculating the number of pulses for PCAP
        if forward:
            pulses = N_intervals+1
        else:
            pulses = N_intervals+2 # +1 extra pulse to get an extra interval for the alignment shift
        
        if forward:
            send_parameters = {"PRE_START": int(pre_start), "START": int(start)-width, "WIDTH": width, "STEP": step, "PULSES": pulses}
        else:
            pulses +=1
            send_parameters = {"PRE_START": int(pre_start), "START": int(start+step), "WIDTH": width, "STEP": step, "PULSES": pulses}               
        for parameter in send_parameters.items():
            field_name, value = parameter
            if forward:
                field = 'PCOMP1.' + field_name
            else:
                field = 'PCOMP2.' + field_name
            resp = self.query(f'{field}={value}')
            print(f'{field}={value} has been sent, response: {resp}')
        resp = self.query('SRGATE1.FORCE_RST=')
        print(f'SRGATE1 RESET {resp}')
        resp = self.query('SRGATE1.FORCE_SET=')
        print(f'SRGATE1 SET {resp}')
        return pulses
    
    def _pcap_enable(self, enable=True):
        if enable:
            resp = self.query('PCAP.ENABLE=ONE')
            print('PCAP ENABLED', resp)
        else:
            resp = self.query('PCAP.ENABLE=ZERO')
            print('PCAP DISABLED', resp)
    
    def prepare_line_scan(self, pre_start, start, stop, N_intervals):
        '''
        This function prepares all of the needed Panda blocks for a continious(fly) line scan according to the provided
        start(µm), stop(µm), and N_intervals values. In case of 2D scans, it has to be called only once to prepare
        the first line. All the subsequent lines should be acuired simply via arm() function. 
        '''
        forward_start = start - 2*(stop-start)/N_intervals
        self._seq1_prepare(forward_start=forward_start, backward_start=stop)
        pulses_f = self._pcomp_prepare(pre_start=pre_start, start=start, stop=stop, N_intervals=N_intervals, forward=True)
        pulses_b = self._pcomp_prepare(pre_start=pre_start, start=stop, stop=start, N_intervals=N_intervals, forward=False)
        self.burst_n = pulses_f + pulses_b
        self._pcap_enable(True)

    def prepare(self, pre_start, start, stop, N_intervals):
        """
        Run before acquisition, once per scan.
        """
        self.prepare_line_scan(pre_start, start, stop, N_intervals)
    
    def start(self):
        """
        Start acquisition when software triggered.
        """
        if self.busy():
            raise Exception('%s is busy!' % self.name)


class PandaBox0D(Detector):
    def __init__(self, name=None, device=None):
        """
        A PandaBox subclasses for 0D detectors, i.e. Photodiode and PMT
        """
        super(PandaBox0D, self).__init__(name=name)
        self.device_name = device
        self._dwell = 10
        self._trigger_state = False
        self._trig_indx = 0
        self._pd_diode_i = 0
        self._pmt_i = 0
        try:
            self.dev = tango.DeviceProxy(self.device_name)
        except Exception as err:
            raise Exception('Faild to initialize withe the error: %s' % err)
        self.dev.subscribe_event("DetOut", tango.EventType.CHANGE_EVENT, self._det_out_cb)
        self.dev.DetTrigCntr = 0

    def _det_out_cb(self, evnt):
        if evnt.attr_value.value is None:
            return
        self._trig_indx, self._pd_diode_i, self._pmt_i = evnt.attr_value.value.tolist()
        #print('DetOut Callback.', evnt.attr_value.value.tolist())
        self._trigger_state = False

    def initialize(self):
        pass

    @property
    def dwell(self):
        """
        Sets dwell time via PULSE2.WIDTH, dwell in ms.

        """
        return self._dwell

    @dwell.setter
    def dwell(self, dwell):
        """
        Sets dwell time via PULSE2.WIDTH, dwell in ms.

        """
        self.dev.DetDwell = dwell
        self._dwell = dwell

    def busy(self):
        if self._trigger_state:
            return True
        else:
            return False

    def prepare(self, acqtime, dataid, n_starts=1):
        if self.busy():
            raise Exception('%s is busy!' % self.name)
        self.dev.DetDwell = acqtime
        self._dwell = acqtime
        self.acqtime = acqtime
        self.n_starts = n_starts
        self.dev.DetTrigCntr = 0

    def start(self):
        """
        Start acquisition when software triggered.
        """
        if self.busy():
            raise Exception('%s is busy!' % self.name)
        self._trigger_state = True
        self.dev.DetTrig = True

    def stop(self):
        pass

    def read(self):
        #return np.array([int(self._trig_indx), int(self._pd_diode_i), int(self._pmt_i)])
        return self._pmt_i