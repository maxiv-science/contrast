from ..Gadget import Gadget
from .. import utils
from ..environment import macro

from multiprocessing import get_context
# Fancy multiprocessing contexts needed or we will crash matplotlib
# and ipython somehow. On the other hand, 'spawn' is more sensitive
# than 'fork' so you have to be careful only to call Recorder.start()
# from main, see the example scripts.
ctx = get_context('spawn')
Queue = ctx.Queue

class Process(ctx.Process):
    """ Dummy for cleaning up the inheritance documentation. """
    pass

import time
import signal

class RecorderHeader(dict):
    """
    Helper class to define a specific dict format to send recorders
    when a new scan starts.
    """
    def __init__(self, scannr, path, snapshot=None, description=None, status=None):
        super(RecorderHeader, self).__init__(scannr=scannr,
                                             status=status,
                                             path=path,
                                             snapshot=snapshot,
                                             description=description)

class RecorderFooter(dict):
    """
    Helper class to define a specific dict format to send recorders
    when a new scan finishes.
    """
    #pass
    def __init__(self, scannr, path, snapshot=None, description=None, status=None):
        super(RecorderFooter, self).__init__(scannr=scannr,
                                             status=status,
                                             path=path,
                                             snapshot=snapshot,
                                             description=description)

class Recorder(Gadget, Process):
    """
    Base class for Recorders. Provides the multiprocessing and queuing
    functionality.
    """
    def __init__(self, delay=.1, **kwargs):
        """
        :param delay: Sleep time for the queue checking loop.
        :type delay: float
        :param ``**kwargs``: Passed on to base class constructor
        """
        Process.__init__(self)
        Gadget.__init__(self, **kwargs)
        ctx = get_context('spawn')
        self.queue = ctx.Queue()
        self.delay = delay
        self.quit = False

    def _process_queue(self):
        dcts = []
        while not self.queue.empty():
            dcts.append(self.queue.get()) # ok since only we are reading from self.queue
        for dct in dcts:
            if dct is None:
                self.quit = True
            elif isinstance(dct, RecorderHeader):
                self.act_on_header(dct)
            elif isinstance(dct, RecorderFooter):
                self.act_on_footer(dct)
            else:
                self.act_on_data(dct)

    def run(self):
        """
        The main loop of the recorder.
        """
        # ignore SIGINT signals from ctrl-C in the main process
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        self.init()
        while not self.quit:
            time.sleep(self.delay)
            self._process_queue()
            self.periodic_check()
        self._close()

    def init(self):
        """
        *Override this.* Use this method to Initialize the recorder
        (open windows, open files, etc.).
        """
        pass

    def act_on_header(self, dct):
        """
        *Override this.* Performs an action when a new scan is started.
        The key-value pairs of dct are defined by RecorderHeader.
        """
        pass

    def act_on_data(self, dct):
        """
        *Override this.* Performs an action when a new data package is
        received. The keys of dct are detector and motor names, the
        values are their readings at one particular point in the scan.
        """
        pass

    def act_on_footer(self, dct):
        """
        *Override this.* Performs an action when a scan ends.
        """
        pass

    def periodic_check(self):
        """
        A function which gets called on every iteration of the recorder.
        Useful for example for checking if files should be closed or
        whether a plot window still exists.
        """

    def _close(self):
        """
        *Override this.* Clean up (close windows, close files...)
        """
        pass

    def stop(self):
        """
        Stop a started subprocess safely by putting a poison pill in
        its queue.
        """
        self.queue.put(None)


class DummyRecorder(Recorder):
    """
    Dummy recorder for practise.
    """
    def act_on_header(self, dct):
        print('got a header! am told to write scan %d to %s' % (dct['scannr'], dct['path']))
    def act_on_data(self, dct):
        print('found this!', dct)
    def act_on_footer(self, dct):
        print('scan %d at %s over, apparently' % (dct['scannr'], dct['path']))
    def init(self):
        print('opening')
    def _close(self):
        print('closing')


def active_recorders():
    """
    Utilify function which returns a list of currently running
    ``Recorder`` objects.

    """
    return [r for r in Recorder.getinstances() if r.is_alive()]

@macro
class LsRec(object):
    """
    List active recorders.
    """
    def run(self):
        dct = {r.name: r.__class__ for r in active_recorders()}
        print(utils.dict_to_table(dct, titles=('name', 'class')))
