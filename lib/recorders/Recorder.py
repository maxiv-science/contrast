from ..Gadget import Gadget
from .. import utils
from ..environment import macro

from multiprocessing import get_context
# Fancy multiprocessing contexts needed or we will crash matplotlib
# and ipython somehow. On the other hand, 'spawn' is more sensitive
# than 'fork' so you have to be careful only to call Recorder.start()
# from main, see the example scripts.
ctx = get_context('spawn')
Process = ctx.Process
Queue = ctx.Queue

import time
import signal

class Recorder(Gadget, Process):
    """
    Base class for Recorders. Provides the multiprocessing and queuing
    functionality.
    """
    def __init__(self, name=None, delay=.1):
        Process.__init__(self)
        Gadget.__init__(self, name=name)
        ctx = get_context('spawn')
        self.queue = ctx.Queue()
        self.delay = delay
        self.quit = False
        self.sleep_fcn = time.sleep

    def run(self):
        # ignore SIGINT signals from ctrl-C in the main process
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        self.init()
        while not self.quit:
            self.sleep_fcn(self.delay)
            dcts = [self.queue.get() for i in range(self.queue.qsize())] # ok since only we are reading from self.queue
            for dct in dcts:
                if not dct:
                    self.quit = True
                else:
                    self.act_on_data(dct)
            self.periodic_check()
        self.close()

    def init(self):
        """
        Subclass this. Initialize (open windows, open files, ...)
        """
        pass

    def act_on_data(self):
        """
        Subclass this. Performs an action when a new data package is
        received.
        """
        pass

    def close(self):
        """
        Subclass this. Clean up (close windows, close files...)
        """
        pass

    def stop(self):
        """
        Stop a started subprocess safely by putting a poison pill in
        its queue.
        """
        self.queue.put(None)


class DummyRecorder(Recorder):
    def act_on_data(self, dct):
        print('found this!', dct)
    def init(self):
        print('opening')
    def close(self):
        print('closing')


def active_recorders():
    return [r for r in Recorder.getinstances() if r.is_alive()]

@macro
class LsRec(object):
    """
    List active recorders.
    """
    def run(self):
        dct = {r.name: r.__class__ for r in active_recorders()}
        print(utils.dict_to_table(dct, titles=('name', 'class')))
