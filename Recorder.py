from Gadget import Gadget
import utils

from multiprocessing import get_context
# Fancy multiprocessing contexts needed or we will crash matplotlib
# and ipython somehow. On the other hand, 'spawn' is more sensitive
# than 'fork' so you have to be careful only to call Recorder.start()
# from main, see the example scripts.
ctx = get_context('spawn')
Process = ctx.Process
Queue = ctx.Queue

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
plt.ion()

print(__name__)

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

    def run(self):
        self.init()
        while not self.quit:
            plt.pause(self.delay)
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


class DummyRecorder(Recorder):
    def act_on_data(self, dct):
        print('found this!', dct)
    def init(self):
        print('opening')
    def close(self):
        print('closing')

class PlotRecorder(Recorder):

    def __init__(self, xdata, ydata, name='plot'):
        #super(PlotRecorder, self).__init__(name='plotrecorder')
        Recorder.__init__(self, name=name)
        self.xdata = xdata
        self.ydata = ydata
        self.nplots = 0

    def init(self):
        self.fig = plt.figure()
        self.fig.canvas.set_window_title(self.name)
        self.ax = self.fig.gca()
        plt.pause(.1)
        self.scannr = None

    def act_on_data(self, dct):
        if not dct['scannr'] == self.scannr:
            self.nplots += 1
            self.scannr = dct['scannr']
            self.x, self.y = [], []
            col = 'bkmrcg'[(self.nplots-1) % 6]
            self.l = Line2D(xdata=[], ydata=[], color=col)
            self.ax.add_line(self.l)
        self.l.set_data(self.x, self.y)
        self.x.append(dct[self.xdata])
        self.y.append(dct[self.ydata])
        self.ax.relim()
        self.ax.autoscale_view()
        plt.draw()
        plt.pause(.01)

    def periodic_check(self):
        if not plt.fignum_exists(self.fig.number):
            self.quit = True

    def close(self):
        plt.close(self.fig)

