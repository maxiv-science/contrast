"""
Basic class for treating a PandaBox as a detector, capable
of operating in burst mode (thereby acting as a time-based
trigger source).

The PandaBox is infinitely configurable, and this class assumes that:
1) the PCAP block is used,
2) the PULSE1 block is used to control the number of
   acquired points and their timing, and
3) flickering the "A" bit causes a trigger.

"""

from .Detector import Detector, TriggeredDetector, BurstDetector
from ..environment import env

import time
import numpy as np
import socket
from threading import Thread

SOCK_RECV = 4096

class PandaBox(Detector, TriggeredDetector, BurstDetector):

    def __init__(self, name=None, host='172.16.126.88',
                 ctrl_port=8888, data_port=8889):
        """
        Class to interact directly with the Eiger Simplon API.
        """
        self.host = host
        self.ctrl_port = ctrl_port
        self.data_port = data_port
        self.acqthread = None
        Detector.__init__(self, name=name)
        TriggeredDetector.__init__(self)
        BurstDetector.__init__(self)

    def initialize(self):
        self.ctrl_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ctrl_sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
        self.ctrl_sock.settimeout(1)
        self.ctrl_sock.connect((self.host, self.ctrl_port))

    def query(self, cmd):
        self.sock.sendall(bytes(cmd + '\n', 'ascii'))
        return self.sock.recv(SOCK_RECV).decode()

    def busy(self):
        # TODO: possibly disarm here
        if self.acqthread and self.acqthread.is_alive():
            return True

    def prepare(self, acqtime, dataid, n_starts):
        """
        Run before acquisition, once per scan.
        """
        # TODO: set the number of images and the timing
        pass

    def arm(self):
        """
        Gets called before every start command
        """
        self.acqthread = Thread(target=self._acquire)
        self.acqthread.start()
        # TODO: arm the PCAP block here
        pass

    def _acquire(self, N):
        """
        Receive and parse one set of measurements.
        """
        # TODO: connect and get the header, collect the channels
        data = {ch:[] for ch in channels}
        n = 0
        while n < self.burst_n:
            # TODO: receive everything and append to the lists in data
            pass
        self.data = data

    def start(self):
        """
        Start acquisition when software triggered.
        """
        if not self.hw_trig:
            pass
            # TODO: here we should flicker the magic bit
        else:
            pass
            # do nothing, we'll get our trigger.

    def stop(self):
        # TODO: disarm
        pass

    def read(self):
        # TODO: return the dict parsed from the streamer
