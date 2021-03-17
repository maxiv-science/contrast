from . import Recorder, RecorderFooter
from .Hdf5Recorder import Link
import zmq
import time

def walk_dict(dct):
    """
    A recursive version of dict.items(), which yields
    (containing-dict, key, val).
    """
    for k, v in dct.items():
        yield dct, k, v
        if isinstance(v, dict):
            for d_, k_, v_ in walk_dict(v):
                yield d_, k_, v_

class StreamRecorder(Recorder):
    """
    Recorder which publishes data to a zmq stream. Try receiving it with::

        import zmq
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.connect ("tcp://localhost:5556")
        socket.setsockopt(zmq.SUBSCRIBE, b"") # subscribe to all topics
        while True:
            messagedata = socket.recv_pyobj()
            print(messagedata)

    The result is a sequence of python objects, of type ``dict`` or ``OrderedDict``. Each ``dict`` contains a ``'status'`` field with one of the following values.

    * ``heartbeat``: a dummy message sent to keep connections alive
    * ``started``: indicates the beginning of a scan
    * ``running``: indicates that this is a data message from an ongoing scan
    * ``finished`` or ``interrupted``: indicates that a scan was either completed or stopped.

    Data messages simply contain all gathered motor and detector data, as placed in the ``Recorder`` queue. For example::

        $ print(dict(socket.recv_pyobj()))

        {'sx': 0.8,
         'det2': <ExternalLink to "entry/measurement/data" in file "/tmp/Dummy_scan_005_image_004.hdf5",
         'det1': 0.024625569499185596,
         'dt': 2.3689677715301514,
         'status': 'running'}

    """
    def __init__(self, name=None, port=5556):
        super(StreamRecorder, self).__init__(name=name)
        self.last_heartbeat = time.time()
        self.port = port

    def run(self):
        context = zmq.Context()
        self.socket = context.socket(zmq.PUB)
        self.socket.bind("tcp://*:%s" % self.port)
        super(StreamRecorder, self).run()

    def act_on_header(self, dct):
        """
        Relay information.

        Converts RecorderHeader to plain dict so the receiver doesn't
        need the contrast library.
        """
        self.socket.send_pyobj(dict(dct), protocol=2)

    def act_on_data(self, dct, base='entry/measurement/'):
        """
        Relay information, but filter out exotic objects like Links.
        """
        for d, k, v in walk_dict(dct):
            if isinstance(v, Link):
                d[k] = {'type':'Link',
                        'filename':v.filename,
                        'path':v.path,
                        'universal':v.universal} 
        dct['status']='running'   
        self.socket.send_pyobj(dct, protocol=2)

    def act_on_footer(self, dct):
        """
        Relay information.
        """
        self.socket.send_pyobj(dict(dct), protocol=2)

    def periodic_check(self):
        check_time = time.time()
        if check_time - self.last_heartbeat > 10.:
            self.socket.send_pyobj({'status':'heartbeat'})
            self.last_heartbeat = check_time
