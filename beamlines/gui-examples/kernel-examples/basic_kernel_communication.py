"""
Rudimentary examples of how to communicate with a remote
kernel in the easiest way via a blocking client.

Start the kernel with `jupyter console` on the same machine.
"""

from jupyter_client import BlockingKernelClient
from jupyter_client.connect import find_connection_file
from queue import Empty


def color_print(*args, color='OKBLUE'):
    lookup = {
        'HEADER': '\033[95m',
        'OKBLUE': '\033[94m',
        'OKCYAN': '\033[96m',
        'OKGREEN': '\033[92m',
        'WARNING': '\033[93m',
        'FAIL': '\033[91m',
        'ENDC': '\033[0m',
        'BOLD': '\033[1m',
        'UNDERLINE': '\033[4m',
    }
    print(lookup[color], end='')
    print(*args, end='')
    print(lookup['ENDC'])


# setup by automatically finding a running kernel
cf = find_connection_file()
client = BlockingKernelClient(connection_file=cf)
client.load_connection_file()
client.start_channels()

# simplest usage - execute statments and check if OK
msgid = client.execute('a = 2')
ret = client.get_shell_msg()
status = ret['content']['status']
if status == 'ok':
    print('statement executed ok')
elif status == 'error':
    ename = ret['content']['ename']
    print('there was a %s exception, which will also appear on the '
          'iopub channel' % ename)

# listen to what's going on in the kernel with blocking calls,
# and take different actions depending on what's arriving
while True:
    try:
        msg = client.get_iopub_msg(timeout=.1)
        msg_type = msg['header']['msg_type']
        if msg_type == 'status':
            color_print('status now', msg['content']['execution_state'],
                        color='OKCYAN')
        elif msg_type == 'execute_input':
            color_print('input [%u]: ' % msg['content']['execution_count'],
                        '"%s"' % msg['content']['code'], color='OKGREEN')
        elif msg_type == 'execute_result':
            color_print('output [%u]: ' % msg['content']['execution_count'],
                        '"%s"' % msg['content']['data']['text/plain'],
                        color='HEADER')
        elif msg_type == 'error':
            ename = msg['content']['ename']
            evalue = msg['content']['evalue']
            color_print('got a %s exception ("%s")' % (ename, evalue),
                        color='FAIL')
        elif msg_type == 'stream':
            color_print('stream:\n', msg['content']['text'], color='WARNING')
        else:
            print('other message of type', msg_type)
            color_print(msg)

    except Empty:
        pass
