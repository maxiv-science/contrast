from . import Recorder, RecorderFooter
import zmq

class StreamRecorder(Recorder):
    """
    Recorder which publishes data to a zmq stream. Try receiving it with:

    import zmq
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect ("tcp://localhost:5556")
    socket.setsockopt(zmq.SUBSCRIBE, b"") # subscribe to all topics
    while True:
        messagedata = socket.recv_pyobj()
        print(messagedata)

    """
    def __init__(self, name=None, port=5556):
        super(StreamRecorder, self).__init__(name=name)
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
        Relay information.
        """
        self.socket.send_pyobj(dct, protocol=2)

    def act_on_footer(self):
        """
        Relay information.
        """
        self.socket.send_pyobj({}, protocol=2)
