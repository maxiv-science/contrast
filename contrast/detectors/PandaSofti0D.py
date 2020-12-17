"""
A PandaBox subclasses for 0D detectors, i.e. Photodiode and PMT

This class assumes that:
1) COUNTER5 is connected to TTLIN5 that is in turn connected to the Alba voltage output for the photodiode
2) COUNTER6 is connected to TTLIN6 that is in turn connected to the V2F on BlackFreq, which is connected to the PMT
3) Dwell time is set via PULSE2.WIDTH given in ms
4) The acquisition is software triggered by PULSE2.TRIG=ONE and should be set to PULSE2.TRIG=ZERO before the next acquisition cycle

"""
from .PandaBox import PandaBox, SOCK_RECV
import time


class PandaBox0D(PandaBox):
    
    def __init__(self, name=None, type='diode', host='b-softimax-panda-0.maxiv.lu.se',
                 ctrl_port=8888, data_port=8889):
        """
        The class inherits the PandaBox to add 0D detectors functionality.
        The type can be either 'diode' or 'PMT'
        """
        super().__init__(name=name, host=host, ctrl_port=ctrl_port, data_port=data_port)
        if type == 'diode':
            self.query_str = 'COUNTER5.OUT?'
        elif type == 'PMT':
            self.query_str = 'COUNTER6.OUT?'
        else:
            self.query_str = 'COUNTER5.OUT?'
        
        self.dwell = 0
    
    def _reset(self):
        """
        Resets the detector before each new acquisiton.
        """
        return self.query('PULSE2.TRIG=ZERO')
    
    def _trig(self):
        """
        Resets the detector before each new acquisiton.
        """
        return self.query('PULSE2.TRIG=ONE')

    def set_dwell(self, dwell):
        """
        Sets dwell time via PULSE2.WIDTH, dwell in ms.

        """
        self.dwell = dwell
        return self.query(f'PULSE2.WIDTH={self.dwell}')
    
    def get_intensity(self):
        """
        Reads the intensity from COUNTER5 that is connected to the photodiode
        """
        self._reset()
        self._trig()
        time.sleep(self.dwell/1000)
        resp = self.query(self.query_str).split('=')
        if resp[0] == 'OK ':
            return int(resp[1])
        else:
            return None
