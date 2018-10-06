from . import Recorder
from ..environment import macro

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
plt.ion()

class PlotRecorder(Recorder):

    def __init__(self, data1, data2=None, name='plot'):
        Recorder.__init__(self, name=name)
        if data2 is not None:
            self.xdata = data1
            self.ydata = data2
        else:
            self.xdata = None
            self.ydata = data1
        self.nplots = 0
        # override the sleeping function, time.sleep would block the GUI.
        self.sleep_fcn = plt.pause

    def init(self):
        self.fig = plt.figure()
        self.fig.canvas.set_window_title(self.name)
        self.ax = self.fig.gca()
        self.ax.set_xlabel(self.xdata)
        self.ax.set_ylabel(self.ydata)
        plt.pause(.1)
        self.scannr = None

    def act_on_data(self, dct):
        if not dct['scannr'] == self.scannr:
            # start a new scan
            self.nplots += 1
            self.scannr = dct['scannr']
            self.x, self.y = [], []
            col = 'bkmrcg'[(self.nplots-1) % 6]
            self.l = Line2D(xdata=[], ydata=[], color=col)
            self.ax.add_line(self.l)
        try:
            # if our data isn't in dct, just move on
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
        plt.pause(.01)

    def periodic_check(self):
        if not plt.fignum_exists(self.fig.number):
            self.quit = True

    def close(self):
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
