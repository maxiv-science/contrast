"""
A minimal contrast GUI which directly runs a beamline and does work
in separate threads. The beamline is defined in bl.py, in the same way
as usual. Recorders aren't in place yet, not sure how to do that.
"""

import sys
import datetime
import numpy as np
from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import (QWidget, QTextEdit, QVBoxLayout,
                             QHBoxLayout, QApplication, QPushButton,
                             QTreeView, QProgressBar)
from PyQt5.QtGui import QColor, QStandardItemModel, QStandardItem
import pyqtgraph as pg
from queue import Queue
from io import StringIO
from contrast.Gadget import Gadget
from contrast.motors import Motor
from contrast.scans import AScan
from contrast.environment import env
from contrast.recorders import Recorder
from contrast.recorders.Recorder import Queue as MP_Queue

if __name__ == '__main__':
    # recorder suprocesses require this main guard
    import bl


env.paths.directory = '/tmp'


class Example(QWidget):

    def __init__(self):
        super().__init__()

        # make a text window for terminal output
        self.txt = QTextEdit()
        self.txt.setReadOnly(True)

        # do something with a push button
        self.btn = QPushButton('scan')
        self.btn.clicked.connect(self.run_scan)

        # A sort of Gadget widget - here using pyqt's model/view concept
        self.model = GadgetModel()
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.expandAll()

        # A progress bar for scans
        self.progress = QProgressBar()
        self.progress.setMinimum(0)
        self._last_dt = 0

        self.plot = pg.PlotWidget(parent=self, background='white')

        # layout containing these things
        hbox = QHBoxLayout()
        col1 = QVBoxLayout()
        col2 = QVBoxLayout()
        col1.addWidget(self.tree)
        col1.addWidget(self.txt)
        col1.addWidget(self.btn)
        col1.addWidget(self.progress)
        col2.addWidget(self.plot)
        hbox.addLayout(col1)
        hbox.addLayout(col2)
        self.setLayout(hbox)
        self.resize(1200, 700)

        # redirect stdout
        queue = Queue()
        sys.stdout = StreamWriter(queue)
        self.reader = StreamReader(queue)
        self.reader.signal.connect(self.print)
        self.reader.start()

        # a special recorder which generates qt signals
        queue = MP_Queue()
        self.qtrec = PyQtRecorder(queue, name='qtrec')
        self.qtrec.start()
        self.emitter = RecorderEmitter(queue)
        self.emitter.new.connect(self.new_data)
        self.emitter.start()

        # a scan runner object we can refer to,
        self.runner = None

    @pyqtSlot(dict)
    def new_data(self, dct):
        self.txt.setTextColor(QColor('black'))  # for example
        if 'status' in dct.keys():
            # header/footer
            if dct['status'] == 'started':
                self.progress.setValue(0)
        else:
            # update progress bar
            m = self.progress.maximum()
            n = self.progress.value() + 1
            eta = str(datetime.timedelta(
                seconds=(
                    (m - n) * (dct['dt'] - self._last_dt)))).split('.')[0]
            self.progress.setValue(n)
            self.progress.setFormat('%u/%u (done in %s)' % (n, m, eta))
            self._last_dt = dct['dt']
            # plot something
            self.plot.plot([dct['sx']], [dct['det1']], symbol='o', color='k')

    @pyqtSlot(str)
    def print(self, msg):
        """
        Intercepts the stdout signal and adds it to a text box or so.
        """
        self.txt.setTextColor(QColor('gray'))  # for example
        if len(msg) < 2:
            # exclude empty strings
            return
        if '\r' in msg:
            # exclude overwritten text
            return
        self.txt.append(str(msg))

    def run_scan(self):
        """
        Helper method which puts together the scan to run, and launches
        a ScanRunner object.
        """
        if self.runner and self.runner.isRunning():
            return
        N = np.random.randint(5, 40)
        self.progress.setMaximum(N + 1)
        self.runner = ScanRunner(AScan, *[bl.sx, 0, 1, N, .1])
        self.runner.start()


class ScanRunner(QThread):
    """
    Threaded class which takes a contrast scan class and its arguments,
    then creates an instance and runs it in a thread.
    """
    def __init__(self, scan_class, *args, **kwargs):
        super().__init__()
        self.scan_obj = scan_class(*args, **kwargs)

    def run(self):
        self.scan_obj.run()


class StreamWriter(StringIO):
    """
    Replacement for sys.stdout, puts printed strings in a queue.
    """
    def __init__(self, q):
        super().__init__()
        self.q = q

    def write(self, msg):
        self.q.put(msg)


class StreamReader(QThread):
    """
    Reads from StreamWriter's queue and emits a signal when there's
    something new. Then you have stdout converted to a pyqt signal.
    """
    signal = pyqtSignal(str)

    def __init__(self, q):
        super().__init__()
        self.q = q

    def run(self):
        while True:
            msg = self.q.get()
            self.signal.emit(msg)


class GadgetModel(QStandardItemModel):
    """
    Basic PyQT model representing the Gadget tree, could in principle
    be made richer with status and positions, etc.
    """
    def __init__(self):
        super().__init__()
        top = QStandardItem('Gadget')
        self.appendRow(top)
        for sub in Gadget.__subclasses__():
            row = QStandardItem(sub.__name__)
            for g in sub.getinstances():
                row.appendRow(QStandardItem(g.name))
            top.appendRow(row)


class PyQtRecorder(Recorder):
    """
    Recorder which just puts stuff in a queue for RecorderEmitter.
    """
    def __init__(self, out_queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.out_queue = out_queue

    def act_on_header(self, dct):
        self.out_queue.put(dct)

    def act_on_data(self, dct):
        self.out_queue.put(dct)

    def act_on_footer(self, dct):
        self.out_queue.put(dct)


class RecorderEmitter(QThread):
    """
    Reads PyQtRecorder's output queue, effectively turning recorder
    data into qt signals.
    """
    new = pyqtSignal(dict)

    def __init__(self, queue):
        super().__init__()
        self.queue = queue

    def run(self):
        while True:
            item = self.queue.get()
            if item is None:
                return
            self.new.emit(item)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Example()
    ex.show()
    ret = app.exec_()
    # close subprocesses here
    for r in Recorder.getinstances():
        r.stop()
    sys.exit(ret)
