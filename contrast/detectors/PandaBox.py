from .Detector import Detector, TriggeredDetector, BurstDetector
from ..environment import env

import time
import numpy as np
import socket
from threading import Thread
import select

SOCK_RECV = 4096
RECV_DELAY = 1e-4

class PandaBox(Detector, TriggeredDetector, BurstDetector):
    """
    Basic class for treating a PandaBox as a detector, capable
    of operating in burst mode (thereby acting as a time-based
    trigger source).

    The PandaBox is infinitely configurable, and this class assumes that:

    #. the PCAP block is used,
    #. the PULSE1 block is used to control the number of
       acquired points and their timing, and
    #. flickering the "A" bit causes a trigger.
    """

    def __init__(self, name=None, host='172.16.126.88',
                 ctrl_port=8888, data_port=8889):
        self.host = host
        self.ctrl_port = ctrl_port
        self.data_port = data_port
        self.acqthread = None
        self.burst_latency = .003
        Detector.__init__(self, name=name)
        TriggeredDetector.__init__(self)
        BurstDetector.__init__(self)

    def initialize(self):
        self.ctrl_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ctrl_sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
        self.ctrl_sock.settimeout(1)
        self.ctrl_sock.connect((self.host, self.ctrl_port))

    def query(self, cmd):
        self.ctrl_sock.sendall(bytes(cmd + '\n', 'ascii'))
        return self.ctrl_sock.recv(SOCK_RECV).decode()

    def busy(self):
        if self.acqthread and self.acqthread.is_alive():
            return True
        else:
            return False

    def prepare(self, acqtime, dataid, n_starts):
        BurstDetector.prepare(self, acqtime, dataid, n_starts)
        self.query('PULSE1.PULSES=%d' % self.burst_n)
        self.query('PULSE1.WIDTH=%f' % self.acqtime)
        self.query('PULSE1.STEP=%f' % (self.burst_latency+self.acqtime))

    def arm(self):
        self.acqthread = Thread(target=self._acquire)
        self.acqthread.start()
        self.query('*PCAP.ARM=')
        done = False
        while not done:
            ret = self.query('*PCAP.COMPLETION?')
            if 'Busy' in ret:
                done = True
            time.sleep(.005)
        time.sleep(.05) # necessary hack

    def _acquire(self):
        """
        Receive and parse one set of measurements.
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.data_port))
        s.send(b'\n\n')

        # First wait for the header to be complete, and parse it.
        done = False
        buff = b''
        while not done:
            buff += s.recv(SOCK_RECV)
            if b'\n\n' in buff:
                done = True
        header, buff = buff.split(b'\n\n')
        channels = []
        for line in header.split(b'fields:\n')[-1].split(b'\n'):
            ch = line.strip().split()[0].decode()
            op = line.strip().split()[2].decode()
            channels.append(ch + '_' + op)

        # Then put the rest of the data into the same buffer and continue
        n = 0
        data = {ch:[] for ch in channels}
        
        num_points = self.hw_trig_n * self.burst_n

        while n < num_points:
            # anything more to read?
            ready = select.select([s], [], [], RECV_DELAY)[0]
            if ready:
                buff += s.recv(SOCK_RECV)

            #anything more to parse?
            if b'\n' in buff:
                line, buff = buff.split(b'\n', 1)
                vals = line.strip().split()
                for k, v in zip(channels, vals):
                    if b'END' in v:
                        data[k].append(None)
                        n = num_points
                        break
                    data[k].append(float(v))
                n += 1

        for k, v in data.items():
            data[k] = np.array(v)

        self.data = data
        self.query('*PCAP.DISARM=')

    def start(self):
        if not self.hw_trig:
            self.query('BITS.A=1')
            time.sleep(.001)
            self.query('BITS.A=0')

    def stop(self):
        self.query('*PCAP.DISARM=')

    def read(self):
        return self.data
