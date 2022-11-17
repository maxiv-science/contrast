"""
Prototype GUI for stxm acquisition.

Problems found so far:
    * How do we stop scans that run in threads? For now, put an event
      check into the scan loop, but that means existing scans need to
      be modified for GUI use.
    * env object and other things are not thread safe, but can be
      changed from threads, so just be careful.
"""

import sys
import datetime
import time
import numpy as np
from threading import Event
from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot, Qt
from PyQt5.QtWidgets import (QWidget, QTextEdit, QVBoxLayout,
                             QHBoxLayout, QApplication, QPushButton,
                             QTreeView, QProgressBar)
from PyQt5.QtGui import QColor, QStandardItemModel, QStandardItem
import pyqtgraph as pg
from queue import Queue
from io import StringIO
from contrast.Gadget import Gadget
from contrast.motors import Motor
from dummy_scan import StxmScan
from contrast.environment import env
from contrast.recorders import Recorder
from contrast.recorders.Recorder import Queue as MP_Queue
import contrast

if __name__ == '__main__':
    # recorder suprocesses require this main guard
    import bl


env.paths.directory = '/tmp'


class StxmGui(QWidget):

    def __init__(self):
        super().__init__()

        # a global scan stop event
        self.stop_evt = Event()

        # make a text window for terminal output
        self.txt = QTextEdit()
        self.txt.setReadOnly(True)

        # two push buttons
        self.run_btn = QPushButton('scan')
        self.run_btn.clicked.connect(self.run_stxm_scan)
        self.stop_btn = QPushButton('stop')
        self.stop_btn.clicked.connect(self.stop_evt.set)

        # A sort of Gadget widget - here using pyqt's model/view concept
        self.tree = GadgetTree()
        self.monitor = GadgetMonitor()
        self.monitor.update.connect(self.tree.motor_update)
        self.monitor.start()

        # A progress bar for scans
        self.progress = QProgressBar()
        self.progress.setMinimum(0)
        self._last_dt = 0

        # A widget for displaying results
        self.im_view = pg.ImageView(parent=self)

        # layout containing these things
        hbox = QHBoxLayout()
        col1 = QVBoxLayout()
        col2 = QVBoxLayout()
        btns = QHBoxLayout()
        col1.addWidget(self.tree)
        btns.addWidget(self.run_btn)
        btns.addWidget(self.stop_btn)
        btns.addWidget(self.progress)
        col2.addWidget(self.im_view, 2)
        col2.addWidget(self.txt)
        col2.addLayout(btns)
        hbox.addLayout(col1, 1)
        hbox.addLayout(col2, 3)
        self.setLayout(hbox)
        self.resize(1200, 700)

        # redirect stdout
        queue = Queue()
        sys.stdout = StreamWriter(queue)
        self.reader = StreamReader(queue)
        self.reader.signal.connect(self.new_stdout)
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

        # quote
        contrast.wisdom()

    @pyqtSlot(dict)
    def new_data(self, dct):
        """
        Runs when there is a new data signal emitted.
        """
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
            self.stxm_data.append(dct['stxm_det'])
            self.im_view.setImage(np.array(self.stxm_data).T)

    @pyqtSlot(str)
    def new_stdout(self, msg):
        """
        Intercepts the stdout signal and adds it to a text box or so.
        """
        if len(msg) < 2:
            # exclude empty strings
            return
        if '\r' in msg:
            # exclude overwritten text
            return
        self.print(msg, 'gray')

    def print(self, msg, color='black'):
        self.txt.setTextColor(QColor(color))
        self.txt.append(str(msg))

    def run_stxm_scan(self):
        """
        Helper method which puts together the scan to run, and launches
        a ScanRunner object.
        """
        if self.runner and self.runner.isRunning():
            return
        self.stxm_data = []
        LINES = 200
        self.progress.setMaximum(LINES + 1)
        scan_args = [bl.coarsex, 50, 950, 450, bl.coarsey, 50, 650, LINES, .001]
        self.stop_evt.clear()
        self.runner = ScanRunner(StxmScan, *scan_args,
                                 stop_event=self.stop_evt)
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


class GadgetMonitor(QThread):
    """
    Helper thread which goes around checking states and positions of
    Gadget objects at regular intervals, and issues signals with the
    results.

    In a real GUI, this would ideally be replaced by something like
    Tango events.
    """
    update = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.motors = list(Motor.getinstances())

    def run(self):
        while True:
            dct = {}
            for m in self.motors:
                dct[m.name] = (m.user_position, m.busy())
            self.update.emit(dct)
            time.sleep(2)


class GadgetTree(QTreeView):
    """
    Basic PyQT tree of gadgets.
    """
    def __init__(self):
        super().__init__()

        model = QStandardItemModel(parent=self)
        model.setHorizontalHeaderLabels(['Name', 'Position', 'Busy'])

        top = QStandardItem('Gadget')
        model.appendRow(top)
        for sub in Gadget.__subclasses__():
            row = QStandardItem(sub.__name__)
            for g in sub.getinstances():
                row.appendRow([QStandardItem(g.name),
                               QStandardItem(),
                               QStandardItem()])
            top.appendRow(row)

        self.model = model
        self.setModel(model)
        self.expandAll()

    def find_index(self, name):
        itm = self.model.findItems(name, flags=Qt.MatchRecursive)[0]
        return self.model.indexFromItem(itm)

    @pyqtSlot(dict)
    def motor_update(self, dct):
        parent = self.find_index('Motor')
        for k, v in dct.items():
            row = self.find_index(k).row()
            for i in (0, 1):
                ind = self.model.index(row, i + 1, parent)
                self.model.setData(ind, str(v[i]))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = StxmGui()
    ex.show()
    ret = app.exec_()
    # close subprocesses here
    for r in Recorder.getinstances():
        r.stop()
    sys.exit(ret)
