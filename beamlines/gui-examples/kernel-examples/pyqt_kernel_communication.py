"""
Minimal example of a PyQt GUI reacting to things happening
on a separate kernel. A listener in a QThread emits custom
signals when a message is received.

Start the kernel with `jupyter console` on the same machine.
"""

import sys
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QWidget, QTextEdit, QVBoxLayout, QApplication
from jupyter_client import BlockingKernelClient
from jupyter_client.connect import find_connection_file


class Client(QThread):

    received = pyqtSignal(dict)  # has to be a class attribute

    def run(self):
        cf = find_connection_file()
        client = BlockingKernelClient(connection_file=cf)
        client.load_connection_file()
        client.start_channels(shell=False,
                              iopub=True,
                              stdin=False,
                              control=False,
                              hb=False)
        while True:
            msg = client.get_iopub_msg()
            self.received.emit(msg)


class Example(QWidget):

    def __init__(self):
        super().__init__()

        # set up the GUI
        self.txt = QTextEdit()
        self.txt.setReadOnly(True)

        vbox = QVBoxLayout()
        vbox.addWidget(self.txt)
        self.setLayout(vbox)

        # set up and connect a thread
        self.client = Client()
        self.client.start()
        self.client.received.connect(self.act)

    def act(self, msg):
        msg_type = msg['header']['msg_type']
        if msg_type == 'status':
            pass
        else:
            self.txt.append(msg_type + ':')
            self.txt.append('   ' + str(msg['content']))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Example()
    ex.show()
    sys.exit(app.exec_())
