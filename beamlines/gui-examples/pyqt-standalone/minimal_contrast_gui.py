"""
A minimal contrast GUI which directly runs a beamline and does work
in separate threads. The beamline is defined in bl.py, in the same way
as usual. Recorders aren't in place yet, not sure how to do that.
"""

import sys
from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import (QWidget, QTextEdit, QVBoxLayout,
                             QApplication, QPushButton, QTreeView)
from PyQt5.QtGui import QColor, QStandardItemModel, QStandardItem
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

        # layout
        vbox = QVBoxLayout()
        vbox.addWidget(self.tree)
        vbox.addWidget(self.txt)
        vbox.addWidget(self.btn)
        self.setLayout(vbox)

        # redirect stdout
        queue = Queue()
        sys.stdout = StreamWriter(queue)
        self.reader = StreamReader(queue)
        self.reader.signal.connect(self.print)
        self.reader.start()

        # a special recorder gives qt signals
        queue = MP_Queue()
        self.qtrec = PyQtRecorder(queue, name='qtrec')
        self.qtrec.start()
        self.emitter = RecorderEmitter(queue)
        self.emitter.new.connect(self.testslot)
        self.emitter.start()

        # a scan runner object we can refer to,
        self.runner = None

    @pyqtSlot(dict)
    def testslot(self, dct):
        self.txt.setTextColor(QColor('black'))  # for example
        self.txt.append('got data/header/footer')

    @pyqtSlot(str)
    def print(self, msg):
        """
        Intercepts the stdout signal and adds it to a text box or so.
        """
        self.txt.setTextColor(QColor('red'))  # for example
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
        self.runner = ScanRunner(AScan, *[bl.sx, 0, 1, 10, .1])
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
