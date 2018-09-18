from . import Recorder
from ..environment import macro

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
plt.ion()

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
        try:
            self.x.append(dct[self.xdata])
            self.y.append(dct[self.ydata])
        except KeyError:
            return
        self.l.set_data(self.x, self.y)
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
    def __init__(self, xdata, ydata):
        basename = 'name'
        name = basename
        i = 2
        while name in [r.name for r in Recorder.getinstances()]:
            name = basename + '_%d' % i
            i += 1
        self.xdata = xdata.name
        self.ydata = ydata.name
        self.name = name
    def run(self):
        rec = PlotRecorder(self.xdata, self.ydata, self.name)
        rec.start()
