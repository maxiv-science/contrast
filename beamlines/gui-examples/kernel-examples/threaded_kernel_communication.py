"""
Simple example of wrapping a blocking kernel client in a
thread, and using queues for communication with the main
thread.

Start the kernel with `jupyter console` on the same machine.
"""

from jupyter_client import BlockingKernelClient
from jupyter_client.connect import find_connection_file
from queue import Empty, Queue
from threading import Thread

TIMEOUT = .05


class Client(Thread):
    """
    Takes three queue objects:
    cmd_queue:  input commands to execute
    ctrl_queue: status on executed commands
    pub_queue:  info on all the kernel's doings from iopub

    Pass None as command to quit.
    """
    def __init__(self, cmd_queue, ctrl_queue, pub_queue):
        self.cmd_q = cmd_queue
        self.ctrl_q = ctrl_queue
        self.pub_q = pub_queue
        super().__init__()

    def run(self):
        cf = find_connection_file()
        client = BlockingKernelClient(connection_file=cf)
        client.load_connection_file()
        client.start_channels(shell=False,
                              iopub=True,
                              stdin=False,
                              control=True,
                              hb=False)
        while True:
            try:
                msg = client.get_iopub_msg(TIMEOUT)
                self.pub_q.put(msg)
            except Empty:
                pass
            if self.cmd_q.qsize():
                cmd = self.cmd_q.get()
                if cmd is None:
                    print('Client thread closing')
                    break
                client.execute(cmd)
                self.ctrl_q.put(client.get_shell_msg())


if __name__ == '__main__':
    cmd_q = Queue()
    ctrl_q = Queue()
    pub_q = Queue()
    c = Client(cmd_q, ctrl_q, pub_q)
    c.start()
    cmd_q.put('a = 145')
    res = ctrl_q.get()
    assert res['content']['status'] == 'ok'
