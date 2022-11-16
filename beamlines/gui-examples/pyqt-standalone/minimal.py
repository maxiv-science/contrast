"""
An minimal contrast GUI which directly runs a beamline and does work
in a separate thread. Just a button which runs a scan.
"""

import sys
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QWidget, QApplication, QPushButton
from contrast.scans import AScan
from contrast.motors import DummyMotor
from contrast.detectors import DummyDetector

mot1 = DummyMotor(name='mot1')
det1 = DummyDetector(name='det1')


class Example(QPushButton):

    def __init__(self):
        super().__init__('Push me to run a scan')
        self.clicked.connect(self.run_scan)

    def run_scan(self):
        self.runner = ScanRunner(AScan, *[mot1, 0, 1, 10, .1])
        self.runner.start()


class ScanRunner(QThread):

    def __init__(self, scan_class, *args, **kwargs):
        super().__init__()
        self.scan_obj = scan_class(*args, **kwargs)

    def run(self):
        self.scan_obj.run()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Example()
    ex.show()
    ret = app.exec_()
    sys.exit(ret)
