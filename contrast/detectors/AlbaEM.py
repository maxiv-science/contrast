"""
This module contains an interface to the Alba electrometer, as well as
a contrast Detector class representing it.

Requires the "STREAMING" mode now available as standard firmware.

For the old school data-polling version, see LegacyAlbaEM.py.
"""

if __name__ == '__main__':
    from contrast.detectors import (Detector, LiveDetector, TriggeredDetector,
                                    BurstDetector)
else:
    from .Detector import (Detector, LiveDetector, TriggeredDetector,
                           BurstDetector)
import telnetlib
import numpy as np
import time
import select
from threading import Thread
import zmq
import json

BUF_SIZE = 1024
NUM_CHAN = 4
TIMEOUT = 5
STREAM_PORT = 22003
CMD_PORT = 5025
VALID_RANGE_STRINGS = [
    '1mA', '100nA', '10nA', '1nA', '100uA', '10uA', '1uA', '100pA']
VALID_FILTER_STRINGS = ['3200Hz', '100Hz', '10Hz', '1Hz', '0.5Hz']
BUSY_STATES = ('STATE_RUNNING', 'STATE_ACQUIRING')
IDLE_STATES = ('STATE_ON', )


class Stream(Thread):
    """
    Server which receives the electrometer stream.
    """
    def __init__(self, host, port, debug=False):
        super().__init__()
        context = zmq.Context()
        self.sock = context.socket(zmq.PULL)
        self.sock.set_hwm(10000000)
        self.sock.connect('tcp://%s:%s' % (host, port))
        self.data = []
        self.do_debug = debug

    def debug(self, *args):
        if self.do_debug:
            print(*args)

    def run(self):
        keys = ['timestamp'] + ['CHAN%02u' % (i + 1) for i in range(NUM_CHAN)]
        while True:
            msg = json.loads(self.sock.recv())
            if msg['message_type'] == 'series-start':
                self.data.clear()
            elif msg['message_type'] == 'data':
                self.data.append([msg[key] for key in keys])


class Electrometer(object):
    """
    Interface to a 4-channel Alba electrometer.
    """

    def __init__(self, host='b-nanomax-em2-2', port=CMD_PORT,
                 trig_source='DIO_1', streaming=False,
                 stream_host=None, stream_port=STREAM_PORT):
        try:
            self.em = telnetlib.Telnet(host, port, timeout=5)
        except telnetlib.socket.timeout:
            raise Exception('Could not connect to %s:%d' % (host, port))
        self.query('ACQU:MODE STREAMING')
        # the DIO channel used for triggering:
        self._trig_source = trig_source
        self._host = host
        self.data = []
        self.pull_sock = None
        self.ndata = 0
        # require SW version 2.2.02 where zmq streaming is available,
        # below 2.0.04 soft triggers were broken and below 2.0.0 data
        # indexing was wrong.
        assert self.version >= (2, 2, 2), \
            "Requires on-board SW version 2.2.02 or higher."
        if streaming:
            self.context = zmq.Context()
            #self.stream = Stream(host=host, port=stream_port, debug=False)
            #self.stream.start()
        else:
            self.stream = None

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
        ok = False
        while not ok:
            reply = self.em.read_until(
                b'\r\n', timeout=TIMEOUT).strip().decode('utf-8')
            if reply:
                ok = True
            else:
                print('AlbaEM failed to respond in %.1f s. Trying again...' % TIMEOUT)
        return reply

    def get_instant_current(self, ch):
        return float(self.query('CHAN%02u:INSC?' % ch))

    def get_current_range(self, ch):
        return self.query('CHAN%02u:CABO:RANG?' % ch)

    def set_current_range(self, ch, val):
        if val not in VALID_RANGE_STRINGS:
            return
        self.query('CHAN%02u:CABO:RANG %s' % (ch, val))

    def get_autorange(self, ch):
        lookup = {'On': True, 'Off': False}
        return lookup[self.query('CHAN%02u:CABO:ARNG?' % ch)]

    def set_autorange(self, ch, val):
        val = {True: 'On', False: 'Off'}[bool(val)]
        self.query('CHAN%02u:CABO:ARNG %s' % (ch, val))

    def get_filter(self, ch):
        return self.query('CHAN%02u:CABO:FILT?' % ch)

    def set_filter(self, ch, val):
        if val not in VALID_FILTER_STRINGS:
            return
        self.query('CHAN%02u:CABO:FILT %s' % (ch, val))

    def state(self):
        st = self.query('ACQU:STAT?')
        return st

    def stop(self):
        self.query('ACQU:STOP True')

    def status(self):
        return self.query('ACQU:STUS?')

    def get_acqtime(self):
        return float(self.query('ACQU:TIME?')) * 1e-3

    def set_acqtime(self, val):
        val = val * 1000  # ms
        val = max(val, 0.320)
        self.query('ACQU:TIME %f' % val)

    def prepare(self, acqtime, n_starts, burst_n, latency=320e-6, hw=False, burst=False):
        self.ndata = 0
        self.data.clear()
        self.pull_sock = self.context.socket(zmq.PULL)
        self.pull_sock.connect(f'tcp://{self._host}:22003')

        self.query('ACQU:TIME %f' % (acqtime * 1000)) # in ms
        self.query('ACQU:LOWT %f' % (latency * 1000)) # in ms
        self.total_frames = n_starts * burst_n
        self.query('ACQU:NTRI %u' % self.total_frames)
        self.query('TRIG:DELA 0.0')
        if burst:
            self.query('TRIG:MODE AUTOTRIGGER')
        else:
            self.query('TRIG:MODE %s' % ('HARDWARE' if hw else 'SOFTWARE'))
        self.query('ACQU:STAR')

    # non blocking
    def read(self):
        if self.pull_sock is None:
            return
        keys = ['timestamp'] + ['CHAN%02u' % (i + 1) for i in range(NUM_CHAN)]
        while not self.pull_sock.closed and self.pull_sock.poll(0):
            msg = self.pull_sock.recv_json()
            if msg['message_type'] == 'data':
                self.data.append([msg[key] for key in keys])
                self.ndata += 1
                if self.ndata == self.total_frames:
                    self.pull_sock.close()

    def soft_trigger(self):
        old = int(self.query('ACQU:NDAT?'))
        ret = self.query('TRIG:SWSE True')
        # there's a problem with missing soft triggers in fast buffer
        # mode, but this seems to do it. NDAT cannot be used to check
        # if an acquisition is ready, but waiting for the number to
        # go up seems to ensure that the device will not miss any more
        # commands.
        while int(self.query('ACQU:NDAT?')) == old:
            time.sleep(.001)
        assert ret == 'ACK'

    @property
    def version(self):
        res = self.query('*IDN?')
        version = res.split(',')[-1].strip()
        return tuple(map(int, version.split('.')[:3]))

    def test_soft_triggers(self, N=1000):
        """
        The soft triggering wasn't reliable up until SW version 2.0.0,
        and seems to have started working from 2.0.04. This procedure
        typically halted after a few 100 points.
        """
        self.arm(n=N, acqtime=.001)
        for i in range(N):
            print('starting loop #%u' % (i + 1))
            n = self.ndata
            while n < i:
                print('   only have %u, trying again' % (n,))
                time.sleep(.01)
                n = self.ndata
            print('   have %u, issuing trigger #%u' % (n, i + 1))
            t0 = time.time()
            self.soft_trigger()
            print('soft trigger took %.1f ms' % ((time.time() - t0) * 1000))


class AlbaEM(Detector, LiveDetector, TriggeredDetector, BurstDetector):
    """
    Contrast interface to the alba EM.

    The specifics of the EM enables these four cases, each of which
    causes a different triggering and readout behaviour below:

    1) HW triggered expecting one trigger per SW step -> arm at the top
    2) HW triggered expecting hw_trig_n triggers per SW step -> arm on
       every sw step
    3) Burst mode, burst_n > 1, uses a special EM command
    4) Software triggered mode, -> arm at the top

    Note that the electrometer itself
    (as of SW version 2.0.04) does not allow for triggered burst
    acquisition, as reflected in the code.
    """
    def __init__(self, name=None, debug=False, **kwargs):
        self.kwargs = kwargs
        self.do_debug = debug
        Detector.__init__(self, name=name)
        LiveDetector.__init__(self)
        TriggeredDetector.__init__(self)
        BurstDetector.__init__(self)

    def initialize(self):
        self.em = Electrometer(stream_port=STREAM_PORT,
                               streaming=True, **self.kwargs)
        self.burst_latency = 320e-6
        self.n_started = 0
        self.channels = [ch + 1 for ch in range(NUM_CHAN)]

    def prepare(self, acqtime, dataid, n_starts):
        BurstDetector.prepare(self, acqtime, dataid, n_starts)
        self.n_started = 0
        self.n_starts = n_starts
        if self.busy():
            raise Exception('%s is busy!' % self.name)
        msg = (
            "The Alba EM cannot handle hardware-triggered burst acquisitions!")
        assert not (self.hw_trig and (self.burst_n > 1)), msg
        if self.global_arm:
            self.armed_so_far = 0
            self.repetitions = self.hw_trig_n if self.hw_trig else 1
            self.em.prepare(self.acqtime, self.n_starts, self.repetitions, hw=self.hw_trig)

    @property
    def global_arm(self):
        # This checks whether to arm the EM for several SW starts.
        # This corresponds to cases 1 and 4 (above).
        return self.burst_n <= 1
        #return ((self.hw_trig and self.hw_trig_n == 1)
        #        or (not self.hw_trig and self.burst_n == 1))

    def start_live(self, acqtime=1.0):
        # The Alba EM:s are always in live mode, exposing the "instant
        # current" values.
        pass

    def stop_live(self):
        # Nothing to do...
        pass

    def arm(self):
        pass

    def start(self):
        self.n_started += self.repetitions
        if self.hw_trig:
            return
        elif self.burst_n > 1:
            period = self.acqtime + self.burst_latency
            self.em.prepare(period, 1, self.burst_n, self.burst_latency, burst=True)
        else:
            self.em.soft_trigger()

    def stop(self):
        self.em.stop()
        while self.busy():
            time.sleep(.01)

    def busy(self):
        st = self.em.state()
        if st in IDLE_STATES:
            return False
        self.em.read()
        if self.global_arm:
            # case 1 or 4 (above): expect one point per start on the stream
            return (self.em.ndata < self.n_started)
        else:
            # case 2 or 3 (see above): require an idle status
            return st in BUSY_STATES
        assert(False), "Should never get here!"

    def read(self):
        keys = ['t', ] + self.channels
        data = np.array(self.em.data)
        self.em.data.clear()
        ret={}
        for i in range(len(keys)):
            values = data[:, i]
            if self.burst_n > 1:
                values = values.reshape((1, -1))
            ret[keys[i]] = values
        return ret


if __name__ == '__main__':
    # Example usage of the bare Electrometer class. Currents in uA.
    em = Electrometer(host='b-nanomax-em2-0')
    em.burst(period=.001, n=60000)  # 1 minute, 1 kHz
    while em.ndata < 60000:
        print('Now have %u points' % len(em.stream.data))
        time.sleep(.1)
