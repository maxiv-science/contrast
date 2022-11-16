"""
Client which sends commands to a trivial server and gets data over the
StreamingRecorder.
"""

import zmq
import json

# set up the command socket
context = zmq.Context()
csocket = context.socket(zmq.REQ)
csocket.connect("tcp://localhost:5678")

# set up the data socket
dsocket = context.socket(zmq.SUB)
dsocket.connect("tcp://localhost:5556")
dsocket.setsockopt(zmq.SUBSCRIBE, b"")  # subscribe to all topics

# run a scan
N = 10
csocket.send(('ascan mot1 0 1 %u .1' % N).encode())

# watch the data stream for progress
data = []
while len(data) < (N + 1):
    data.append(dsocket.recv_pyobj())
    print('%u/11\r' % len(data), end='')
print('')

# get the scan's return value to complete the REQ/REP scheme
print('Macro result: %s' % json.loads(csocket.recv()))
