"""
Simple server which listens to macros commands over zmq, and executes
them in the current session.
"""

import zmq
from contrast.environment import runCommand, macro, env
from contrast.motors import DummyMotor
from contrast.detectors import DummyDetector
from contrast.recorders import StreamRecorder
import json

PORT = 5678
mot1 = DummyMotor(name='mot1')
det1 = DummyDetector(name='det1')
if __name__ == '__main__':
    rec = StreamRecorder(name='rec')
    rec.start()


@macro
class MacroServer(object):
    """
    Trivial server which takes macro commands and executes them.
    """
    def __init__(self):
        context = zmq.Context()
        self.socket = context.socket(zmq.REP)
        self.socket.bind("tcp://*:%s" % PORT)

    def run(self):
        while True:
            cmd = self.socket.recv().decode()
            runCommand(cmd)
            self.socket.send(json.dumps(env.lastMacroResult).encode())
