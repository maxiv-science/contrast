"""
This module contains an interface to the Alba electrometer, as well as
a contrast Detector class representing it.
"""

from .Detector import Detector, LiveDetector, TriggeredDetector, BurstDetector
import telnetlib
import numpy as np
import time

NUM_CHAN = 4
TIMEOUT = None
VALID_RANGE_STRINGS = ['1mA', '100nA', '10nA', '1nA', '100uA', '10uA', '1uA', '100pA']
VALID_FILTER_STRINGS = ['3200Hz', '100Hz', '10Hz', '1Hz', '0.5Hz']
BUSY_STATES = ('STATE_RUNNING', 'STATE_ACQUIRING')
IDLE_STATES = ('STATE_ON', )

class Electrometer(object):
    """
    Interface to a 4-channel Alba electrometer.
    """

    def __init__(self, host='b-nanomax-em2-2', port=5025,
                 max_data_points=1000, trig_source='DIO_1'):
        self.em = telnetlib.Telnet(host, port)
        self.query('ACQU:MODE CURRENT')
        # the number of points that the tiny alba RAM can store:
        self._max_data_points = max_data_points
        # the DIO channel used for triggering:
        self._trig_source = trig_source
        # require SW version 2.0.04, below that soft triggers are broken
        # and below 2.0.0 data indexing is wrong.
        assert self.version >= (2, 0, 4), "Requires on-board SW version 2.0.04 or higher."

    def _flush(self):
        return self.em.read_eager().strip().decode('utf-8')

    def query(self, cmd):
        """
        Issue a command and read the answer.
        """
        # ctrl-c during a previous query can have left stuff to be read:
        self._flush()
        cmd = (cmd + '\n').encode('utf-8')
        self.em.write(cmd)
        reply = self.em.read_until(b'\r\n', timeout=TIMEOUT).strip().decode('utf-8')
        if reply:
            return reply
        else:
            return None

    def get_instant_current(self, ch):
        return float(self.query('CHAN%02u:INSC?'%ch))

    def get_current_range(self, ch):
        return self.query('CHAN%02u:CABO:RANG?'%ch)

    def set_current_range(self, ch, val):
        if not val in VALID_RANGE_STRINGS:
            return
        self.query('CHAN%02u:CABO:RANG %s'%(ch, val))

    def get_autorange(self, ch):
        lookup = {'On': True, 'Off': False}
        return lookup[self.query('CHAN%02u:CABO:ARNG?'%ch)]

    def set_autorange(self, ch, val):
        val = {True: 'On', False:'Off'}[bool(val)]
        self.query('CHAN%02u:CABO:ARNG %s'%(ch, val))

    def get_filter(self, ch):
        return self.query('CHAN%02u:CABO:FILT?'%ch)

    def set_filter(self, ch, val):
        if not val in VALID_FILTER_STRINGS:
            return
        self.query('CHAN%02u:CABO:FILT %s'%(ch, val))

    def state(self):
        st = self.query('ACQU:STAT?')
        return st

    def stop(self):
        self.query('ACQU:STOP True')

    def status(self):
        return self.query('ACQU:STUS?')

    def set_acqtime(self, val):
        val = val * 1000 # ms
        val = max(val, 0.320)
        self.query('ACQU:TIME %f'%val)

    def burst(self, period=1., n=1, latency=320e-6):
        """
        Take a series of measurements with internal timing. No
        triggering is possible, the series starts immediately.
        """
        assert n <= self._max_data_points, ("Can't do more than %u points"%self._max_data_points)
        latency = max(latency, .320e-3)
        acqtime = period - latency
        self.query('ACQU:TIME %f'%(acqtime*1000))
        self.query('ACQU:LOWT %f'%(latency*1000))
        self.query('TRIG:MODE AUTOTRIGGER')
        self.query('ACQU:NTRI %u'%n)
        self.query('ACQU:STAR True')

    def arm(self, acqtime=1., n=1, hw=False):
        """
        Prepare for hw- or sw-triggered acquisition, n x acqtime.
        """
        assert n <= self._max_data_points, ("Can't do more than %u points"%self._max_data_points)
        acqtime = acqtime * 1000 # ms
        acqtime = max(acqtime, 0.320)
        self.query('ACQU:TIME %f'%acqtime)
        self.query('TRIG:MODE %s' % ('HARDWARE' if hw else 'SOFTWARE'))
        self.query('TRIG:INPU %s'%self._trig_source)
        self.query('TRIG:DELA 0.0') # no delay
        self.query('ACQU:NTRI %u'%n)
        self.query('ACQU:STAR True')

    def soft_trigger(self):
        self.query('TRIG:SWSE True')

    @property
    def ndata(self):
        return int(self.query('ACQU:NDAT?'))

    @property
    def version(self):
        res = self.query('*IDN?')
        version = res.split(',')[-1].strip()
        return tuple(map(int, version.split('.')))

    def read(self, first=None, number=None, timestamps=False):
        """
        Reads out the data and returns a N-by-NUM_CHAN array. Optionally the
        first point and the number of points to read can be specified.
        Getting the timestamps is optional, because it means masses of
        extra ascii data transfer from the alba.
        """
        self.query('TMST %d' % int(timestamps))
        args = ''
        # read everything or juts some values?
        if first is not None:
            args = ' %d' % first
            if number is not None:
                args += ',%d' % number
        # go
        res = eval(self.query('ACQU:MEAS?%s' % args))
        N = len(res[0][1])
        arr = np.empty(shape=(N, NUM_CHAN), dtype=np.float)
        if timestamps:
            dt = np.array(res[1][1])[:,0]
            for ch in range(NUM_CHAN):
                arr[:, ch] = np.array(res[ch][1])[:,1]
            return dt, arr
        else:
            for ch in range(NUM_CHAN):
                arr[:, ch] = np.array(res[ch][1])
            return arr

    def test_soft_triggers(self):
        """
        The soft triggering wasn't reliable up until SW version 2.0.0,
        and seems to have started working from 2.0.04. This procedure
        typically halted after a few 100 points.
        """
        self.arm(n=1000, acqtime=.001)
        for i in range(1000):
            print('starting loop #%u'%(i+1))
            n = self.ndata
            while n < i:
                print('   only have %u, trying again'%n)
                time.sleep(.01)
                n = self.ndata
            print('   have %u, issuing trigger #%u'%(n, i+1))
            self.soft_trigger()


class AlbaEM(Detector, LiveDetector, TriggeredDetector, BurstDetector):
    """
    Contrast interface to the alba EM.

    The specifics of the EM enables these four cases, each of which
    causes a different triggering and readout behaviour below:

    * HW triggered expecting one trigger per SW step -> arm at the top
    * HW triggered expecting hw_trig_n triggers per step -> arm on every sw step
    * Burst mode, burst_n > 1, uses a special EM command.
    * Software triggered mode, armed at the top

    Note that the electrometer itself
    (as of SW version 2.0.04) does not allow for triggered burst
    acquisition, as reflected in the code.
    """
    def __init__(self, name=None, **kwargs):
        self.kwargs = kwargs
        Detector.__init__(self, name=name)
        LiveDetector.__init__(self)
        TriggeredDetector.__init__(self)
        BurstDetector.__init__(self)

    def initialize(self):
        self.em = Electrometer(**self.kwargs)
        self.burst_latency = 320e-6
        self.n_started = 0
        self.n_started_since_rearm = 0

    def prepare(self, acqtime, dataid, n_starts):
        BurstDetector.prepare(self, acqtime, dataid, n_starts)
        self.n_started = 0
        self.n_starts = n_starts
        if self.busy():
            raise Exception('%s is busy!' % self.name)
        msg = "The Alba EM cannot handle hardware-triggered burst acquisitions!"
        assert not (self.hw_trig and (self.burst_n > 1)), msg
        if self.global_arm:
            self.armed_so_far = 0
            self.rearm()

    @property
    def global_arm(self):
        # This checks whether to arm the EM for several SW starts, which also
        # implies continually rearming every self.em._max_data_points steps,
        # to work around the tiny buffer of the thing.
        return (self.hw_trig and self.hw_trig_n==1) or (not self.hw_trig and self.burst_n==1)

    def rearm(self):
        # Workaround allowing longer triggered scans than the tiny EM buffer allows.
        triggers_left = self.n_starts - self.n_started
        this_batch = min(triggers_left, self.em._max_data_points)
        self.em.arm(self.acqtime, this_batch, self.hw_trig)
        self.n_started_since_rearm = 0
        self.armed_so_far += this_batch

    def start_live(self, acqtime=1.0):
        # The Alba EM:s are always in live mode, exposing the "instant current" values.
        pass

    def stop_live(self):
        # Nothing to do...
        pass

    def arm(self):
        if (self.hw_trig and self.hw_trig_n>1):
            self.em.arm(self.acqtime, self.hw_trig_n, True)
        if self.global_arm and (self.n_started == self.armed_so_far):
            self.rearm()

    def start(self):
        self.n_started += 1
        self.n_started_since_rearm += 1
        if self.hw_trig:
            return
        elif self.burst_n > 1:
            period = self.acqtime + self.burst_latency
            self.em.burst(period, self.burst_n, self.burst_latency)
        else:
            self.em.soft_trigger()

    def stop(self):
        self.em.stop()
        while self.busy:
            time.sleep(.01)

    def busy(self):
        st = self.em.state()
        if st in IDLE_STATES:
            return False
        if (self.hw_trig and self.hw_trig_n>1) or (self.burst_n > 1):
            return st in BUSY_STATES
        elif self.global_arm:
            return (self.em.ndata < self.n_started_since_rearm)
        assert(False), "Should never get here!"

    def read(self):
        if (self.hw_trig and self.hw_trig_n>1) or (self.burst_n > 1):
            dt, arr = self.em.read(timestamps=True)
            res = {i+1: arr[:, i] for i in range(NUM_CHAN)}
            res['ts'] = dt
        elif self.global_arm:
            first = self.n_started_since_rearm - 1
            dt, arr = self.em.read(first=first, number=1, timestamps=True)
            res = {i+1: arr[0, i] for i in range(NUM_CHAN)}
            res['ts'] = dt[0]
        else:
            assert(False), 'Should never get here!'
        return res
