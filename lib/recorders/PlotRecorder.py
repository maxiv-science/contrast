from . import Recorder
from ..environment import macro

import signal
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


class PlotRecorder(Recorder):
    """
    Recorder which catches data and plots it with matplotlib.

    Unlike the base class Recorder, the GUI event loop takes care of
    the timing (plt.timer) and when to close (plt.show).
    """

    def __init__(self, data1, data2=None, name='plot'):
        Recorder.__init__(self, name=name)
        if data2 is not None:
            self.xdata = data1
            self.ydata = data2
        else:
            self.xdata = None
            self.ydata = data1
        self.nplots = 0

    def init(self):
        # set up figure and axes
        self.fig = plt.figure()
        self.fig.canvas.set_window_title(self.name)
        self.ax = self.fig.gca()
        self.ax.set_xlabel(self.xdata)
        self.ax.set_ylabel(self.ydata)

        # add a timer to trigger periodic checking of the queue
        timer = self.fig.canvas.new_timer(interval=self.delay*1000)
        timer.add_callback(self._timer_callback)
        timer.start()

        # blocking show() manages when the application should close
        plt.show()

    def _timer_callback(self):
        # this SIGINT handling has to be set up here, for some reason
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        self._process_queue()
        self.periodic_check()

    def run(self):
        self.init()

    def act_on_header(self, dct):
        # start a new scan
        self.nplots += 1
        self.x, self.y = [], []
        col = 'bkmrcg'[(self.nplots-1) % 6]
        self.l = Line2D(xdata=[], ydata=[], color=col, label=str(dct['scannr']))
        self.ax.add_line(self.l)
        self.ax.legend()

    def act_on_data(self, dct):
        # if our data isn't in dct, just move on
        try:
            self.y.append(dct[self.ydata])
            if self.xdata is not None:
                # checking if we have explicit x data
                self.x.append(dct[self.xdata])
            else:
                self.x = range(len(self.y))
            self.l.set_data(self.x, self.y)
        except KeyError:
            return
        self.ax.relim()
        self.ax.autoscale_view()
        plt.draw()

    def _close(self):
        plt.close(self.fig)

@macro
class LivePlot(object):
    """
    Start a live plot recorder which will plot coming scans.

    liveplot [<x>] <y>

    Examples:
    liveplot xmotor diode1
    liveplot diode1
    """
    def __init__(self, data1, data2=None):
        basename = 'plot'
        name = basename
        i = 2
        while name in [r.name for r in Recorder.getinstances()]:
            name = basename + '_%d' % i
            i += 1
        self.data1 = data1.name if hasattr(data1, 'name') else data1
        self.data2 = data2.name if hasattr(data2, 'name') else data2
        self.name = name
    def run(self):
        rec = PlotRecorder(data1=self.data1, data2=self.data2, name=self.name)
        rec.start()
