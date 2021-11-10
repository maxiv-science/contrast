from .Detector import Detector, SoftwareLiveDetector, TriggeredDetector, BurstDetector
from ..environment import env
from ..recorders.Hdf5Recorder import Link
import os
import re
import time
import socket
import select

BUF_SIZE = 1024
TIMEOUT = 20

class Pilatus(Detector, SoftwareLiveDetector, TriggeredDetector, BurstDetector):
    """
    Provides an interface to the Pilatus streaming manager,

    https://github.com/maxiv-science/pilatus-streamer
    """

    def __init__(self, hostname, name=None):
        BurstDetector.__init__(self)
        SoftwareLiveDetector.__init__(self)
        TriggeredDetector.__init__(self)
        Detector.__init__(self, name=name) # last so that initialize() can overwrite parent defaults
        self._hdf_path = 'entry/measurement/Pilatus/data'
        self.hostname = hostname

    def initialize(self):
        self._initialize_socket()
        self.imgpath = '/lima_data/'
        self.burst_latency = .003

    def prepare(self, acqtime, dataid, n_starts):
        BurstDetector.prepare(self, acqtime, dataid, n_starts)
        self.arm_number = -1

        if self.busy():
            raise Exception('%s is busy!' % self.name)

        if dataid is None:
            # no saving
            self.saving_file = ''
        else:
            # saving
            path = env.paths.directory
            fn = 'scan_%06d_%s.hdf5' % (dataid, self.name)
            self.saving_file = os.path.join(path, fn)
            if os.path.exists(self.saving_file):
                print('%s: this hdf5 file exists, I am raising an error now'%self.name)
                raise Exception('%s hdf5 file already exists' % self.name)

        self.exptime = self.acqtime
        self.expperiod = self.burst_latency + self.acqtime

    def arm(self):
        if self.busy():
            raise Exception('%s is busy!' % self.name)
        self.arm_number += 1

        if self.hw_trig and (self.burst_n == 1):
            # each image triggered
            self.nimages = self.hw_trig_n
            self._camserver_start(command='extmtrigger', filename=self.saving_file)
        elif self.hw_trig and (self.burst_n > 1):
            # triggered burst mode
            self.nimages = self.burst_n
            self._camserver_start(command='exttrigger', filename=self.saving_file)

    def start(self):
        if self.hw_trig:
            return
        if self.busy():
            raise Exception('%s is busy!' % self.name)
        self.nimages = self.burst_n
        self._camserver_start(command='exposure', filename=self.saving_file)

    def stop(self):
        if not self.busy():
            return
        self.sock.send(b'camcmd k\0')
        buf = ''
        while 'OK' not in buf:
            ready = select.select([self.sock], [], [], TIMEOUT)
            if ready[0]:
                buf += self.sock.recv(BUF_SIZE).decode(encoding='ascii')
            else:
                raise Exception('The camserver didnt accept the stop command. This happens when it is running above 10 Hz or so.')
        self._started = False

    def busy(self):
        if self.sock is None:
            return True
        if not self._started:
            return False

        ready = select.select([self.sock], [], [], 0.0)
        if ready[0]:
            response = self.sock.recv(BUF_SIZE).decode(encoding='ascii')
            if len(response) == 0:
                raise Exception('The socket connecting client to streamer is dead')
            if 'ERR' in response:
                print('Error! The %s acquisition didnt finish. Causing a ctrl-C...'%self.name)
                print('This should be done better, we could actually move on to the next line. But for now lets focus on not halting forever.')
                raise KeyboardInterrupt
            if response.startswith('7 OK'):
                self._started = False
                return False
        return True

    def read(self):
        if self.saving_file == '':
            return None
        else:
            return {'frames': Link(self.saving_file , self._hdf_path, universal=True),
                    'thumbs:': None,}

    def _initialize_socket(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(TIMEOUT)
            self.sock.connect((self.hostname, 8888))
            self._started = False
        except:
            self.sock = None

    def _camserver_start(self, filename='', command='exposure'):
        """
        The command argument can be 'exposure', 'extmtrigger',
        'extenable', 'exttrigger', see the Pilatus manual.
        """
        if self.busy():
            raise Exception('Already running!')
        allowed = ('exposure', 'extmtrigger', 'extenable', 'exttrigger')
        assert command in allowed
        res = self._query('%s %s' % (command, filename), timeout=TIMEOUT)
        if res is None or (not res.startswith('15 OK')) or ('ERR' in res):
            raise Exception('Error starting exposure')
        else:
            self._started = True

    def _query(self, command, timeout=TIMEOUT):
        if self.busy():
            print('Detector measuring, better not...')
            return ''
        self._clear_buffer()
        self.sock.send(bytes(command + '\0', encoding='ascii'))
        ready = select.select([self.sock], [], [], TIMEOUT)
        if ready[0]:
            response = self.sock.recv(BUF_SIZE).decode(encoding='ascii')
        else:
            response = None
        return response

    def _clear_buffer(self):
        """
        Checks that the connection is OK and clears the buffer.
        """
        while True:
            ready = select.select([self.sock], [], [], 0)
            if ready[0]:
                try:
                    dump = self.sock.recv(BUF_SIZE)
                except OSError:
                    self._initialize_socket()
                    return
                if len(dump) == 0:
                    # only happens if the server has been dead
                    print('something is strange - reinitializing the socket!')
                    self._initialize_socket()
            else:
                break

    def _parse_response(self, data, pattern):
        match = re.compile(pattern).match(data)
        ret = match.groups(1)[0] if match else None
        return ret

    @property
    def energy(self):
        """ Operating energy """
        res = self._query('setenergy', timeout=TIMEOUT)
        res = self._parse_response(res, '15 OK Energy setting: (.*) eV')
        energy = float(res) if res else None
        return energy

    @energy.setter
    def energy(self, value):
        res = self._query('setenergy %f' % value, timeout=TIMEOUT)
        if res is None or not res.startswith('15 OK'):
            raise Exception('Error setting energy')

    @property
    def exptime(self):
        res = self._query('exptime')
        res = self._parse_response(res, '15 OK Exposure time set to: (.*) sec.\x18')
        return float(res)

    @exptime.setter
    def exptime(self, value):
        res = self._query('exptime %f' % value)
        if res is None or not res.startswith('15 OK'):
            raise Exception('Error setting exptime')

    @property
    def expperiod(self):
        res = self._query('expperiod')
        res = self._parse_response(res, '15 OK Exposure period set to: (.*) sec\x18')
        return float(res)

    @expperiod.setter
    def expperiod(self, value):
        res = self._query('expperiod %f' % value)
        if res is None or not res.startswith('15 OK'):
            raise Exception('Error setting expperiod')

    @property
    def nimages(self):
        res = self._query('nimages')
        res = self._parse_response(res, '15 OK N images set to: (\d+)')
        nimages = int(res) if res else None
        return nimages

    @nimages.setter
    def nimages(self, value):
        res = self._query('nimages %d' % value)
        if res is None or not res.startswith('15 OK'):
            raise Exception('Error setting nimages')

    @property
    def imgpath(self):
        res = self._query('imgpath')
        res = self._parse_response(res, '10 OK (.*)\x18')
        return res

    @imgpath.setter
    def imgpath(self, value):
        res = self._query('imgpath %s' % value)
        if res is None or not res.startswith('10 OK'):
            raise Exception('Error setting imgpath')

