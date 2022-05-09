from . import Recorder
from ..environment import macro

import signal
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import matplotlib.cm as cm
import matplotlib.animation


def dict_lookup(dct, path):
    """
    Helper to recursively get dct['path']['to']['item'] from
    dct['path/to/item'].
    """
    if '/' in path:
        pre, post = path.split('/', maxsplit=1)
        return dict_lookup(dct[pre], post)
    else:
        return dct[path]

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
        self.timer = self.fig.canvas.new_timer(interval=int(self.delay*1000))
        self.timer.add_callback(self._timer_callback)
        self.timer.start()

        # blocking show() manages when the application should close
        plt.show()

    def _timer_callback(self):
        # this SIGINT handling has to be set up here, for some reason
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        self._process_queue()
        self.periodic_check()
        if self.quit:
            self._close()

    def run(self):
        self.init()

    def act_on_header(self, dct):
        # start a new scan
        self.nplots += 1
        self.x = []
        self.new_scan = True
        self.scannr = dct['scannr']

    def act_on_data(self, dct):
        # if our data isn't in dct, just move on
        try:
            new_data = dict_lookup(dct, self.ydata)
        except KeyError:
            return

        # be ready to get data that are dicts instead of numbers,
        # so may as well just work with dicts.
        if not isinstance(new_data, dict):
            new_data = {'': new_data}

        # we can only set up lines etc once we know what is actually
        # in the data.
        if self.new_scan:
            self.new_scan = False
            col = 'bkmrcg'[(self.nplots-1) % 6]
            styles = {k:['solid', 'dashed', 'dotted', 'dashdot'][i%4] for i, k in enumerate(new_data.keys())}
            self.lines = {key: Line2D(xdata=[], ydata=[], color=col, linestyle=styles[key], label='%d: %s'%(self.scannr, key)) for key in new_data.keys()}
            self.y = {key: [] for key in new_data.keys()}
            for k, l in self.lines.items():
                self.ax.add_line(l)
            self.ax.legend()

        # ok treat the actual data
        for k, v in new_data.items():
            self.y[k].append(v)
        if self.xdata is not None:
            # checking if we have explicit x data
            self.x.append(dct[self.xdata])
        else:
            self.x = range(len(self.y[k]))
        for k, l in self.lines.items():
            l.set_data(self.x, self.y[k])

        self.ax.relim()
        self.ax.autoscale_view()
        plt.draw()

    def _close(self):
        plt.close(self.fig)

class PlotRecorderMesh(Recorder):
    """
    Recorder which catches data and plots it with matplotlib.

    Unlike the base class Recorder, the GUI event loop takes care of
    the timing (plt.timer) and when to close (plt.show).
    """

    def __init__(self, data1, data2, data_z, name='plot'):
        Recorder.__init__(self, name=name)
        self.xdata = data1
        self.ydata = data2
        self.zdata = data_z
        self.nplots = 0
        self._x, self._y, self._z = None, None, None

    def init(self):
        # set up figure and axes
        self.fig = plt.figure()
        self.fig.canvas.set_window_title(self.name)
        self.ax = self.fig.gca()
        self.ax.set_xlabel(self.xdata)
        self.ax.set_ylabel(self.ydata)
        self.ax.set_aspect(1)

        # add a timer to trigger periodic checking of the queue
        self.timer = self.fig.canvas.new_timer(interval=int(self.delay*1000))
        self.timer.add_callback(self._timer_callback)
        self.timer.start()

        # blocking show() manages when the application should close
        plt.show()

    def _timer_callback(self):
        # this SIGINT handling has to be set up here, for some reason
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        self._process_queue()
        self.periodic_check()
        if self.quit:
            self._close()

    def _get_new_point(self, dct, xname='finex', yname='finey', zname='roi'):
        self.entries = list(dct.items())
        x_val = dct[xname]
        y_val = dct[yname]
        z_val = dct[zname]
        #print(f'The input dct in _get_new_point is {dct}')
        return (x_val, y_val, z_val)
    
    def run(self):
        self.init()

    def act_on_header(self, dct):
        # start a new scan
        self.nplots += 1
        self.x = []
        self.new_scan = True
        self.scannr = dct['scannr']

        # Extracting range/interval values from the mesh scan description
        self.desc = dct['description'].split()
        self.xdata_param, self.ydata_param = self.desc[2:5], self.desc[6:9]

        # Some values for convenience
        padding_k = 0.05 # Padding coefficient equals 5%
        self.x_array_size = int(self.xdata_param[2])+1
        self.y_array_size = int(self.ydata_param[2])+1
        self.matrix_size = self.x_array_size * self.y_array_size

        self.x_range = float(self.xdata_param[1]) - float(self.xdata_param[0])
        self.y_range = float(self.ydata_param[1]) - float(self.ydata_param[0])
        self.x_lim_pad = self.x_range * padding_k
        self.y_lim_pad = self.y_range * padding_k
        self.x_range_min =  float(self.xdata_param[0]) - self.x_lim_pad
        self.x_range_max =  float(self.xdata_param[1]) + self.x_lim_pad
        self.y_range_min =  float(self.ydata_param[0]) - self.y_lim_pad
        self.y_range_max =  float(self.ydata_param[1]) + self.y_lim_pad

        self.fig_dpi = self.fig.dpi
        self.mrk_size = 1.3*(self.ax.get_window_extent().width / self.x_array_size * 72. / self.fig_dpi) ** 2
        print(f'self.mrk_size: {self.mrk_size}')
        

        # Allocating space for the data points
        # self.X = np.zeros(shape=(self.matrix_size, ), dtype=np.float64)
        # self.Y = np.zeros(shape=(self.matrix_size, ), dtype=np.float64)
        # self.Z = np.zeros(shape=(self.matrix_size, ), dtype=np.float64)

        self.X, self.Y, self.Z = [], [], []

        self.sc = self.ax.scatter(self.X, self.Y, c=self.Z, marker="o", s=self.mrk_size, cmap='Greys_r')
        
        plt.xlim(self.x_range_min, self.x_range_max)
        plt.ylim(self.y_range_min, self.y_range_max)

        #self.ax.relim()
        #self.ax.autoscale_view()

        plt.colorbar(self.sc)
        #self.sc.remove()
        plt.draw()

        self.point_N = 0

    def act_on_data(self, dct):
        # if our data isn't in dct, just move on
        try:
            new_data = dict_lookup(dct, self.ydata)
        except KeyError:
            return

        # print(f'#### act_on_data call: new_data is: {new_data}')

        # be ready to get data that are dicts instead of numbers,
        # so may as well just work with dicts.
        if not isinstance(new_data, dict):
            new_data = {'': new_data}

        self._x, self._y, self._z = self._get_new_point(dct)

        if self.point_N < self.matrix_size:
            self.X.append(float(self._x))
            self.Y.append(float(self._y))
            self.Z.append(float(self._z))
            self.point_N += 1
        else:
            pass

        #self.sc = self.ax.scatter(self.X, self.Y, c=self.Z, marker="o", s=200, cmap='Greens')
        self.sc.set_offsets(np.c_[np.array(self.X), np.array(self.Y)])
        self.sc.set_array(np.array(self.Z))
        self.sc.autoscale()
        plt.draw()

    def _close(self):
        plt.close(self.fig)

@macro
class LivePlot(object):
    """
    Start a live plot recorder which will plot coming scans. ::

        liveplot [<x>] <y>

    Examples::

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

@macro
class LivePlotMesh(object):
    """
    Start a live plot recorder which will plot coming scans. ::

        liveplotmesh <x> <y> <int>

    Examples::

        liveplotmesh finex finey roi
    """
    def __init__(self, data1, data2, data_z):
        basename = 'plot'
        name = basename
        i = 2
        while name in [r.name for r in Recorder.getinstances()]:
            name = basename + '_%d' % i
            i += 1
        self.data1 = data1.name if hasattr(data1, 'name') else data1
        self.data2 = data2.name if hasattr(data2, 'name') else data2
        self.data_z = data_z.name if hasattr(data_z, 'name') else data_z
        self.name = name
    
    def run(self):
        rec = PlotRecorderMesh(data1=self.data1, data2=self.data2, data_z=self.data_z, name=self.name)
        rec.start()
