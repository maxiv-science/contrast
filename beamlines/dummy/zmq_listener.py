#import zmq
#context = zmq.Context()
#socket = context.socket(zmq.SUB)
#socket.connect ("tcp://localhost:5556")
#socket.setsockopt(zmq.SUBSCRIBE, b"") # subscribe to all topics
#while True:
#    messagedata = socket.recv_pyobj()
#    print(messagedata)

import zmq
import sys
import time

#####################################
## zmq listener
#####################################

class zmq_listener(object):
 
    def __init__(self, host='localhost', port=5556, topic=b"", verbosity=0):
        self.context      = zmq.Context()
        self.socket       = self.context.socket(zmq.SUB) 
        self.socket.connect('tcp://'+host+':'+str(port))
        self.socket.setsockopt(zmq.SUBSCRIBE, b"") # subscribe to all topics
        self.verbosity    = verbosity                          
        self.running      = True
        self.run()

    def run(self):

    	

        while self.running:
            try:
                _metadata = self.socket.recv_pyobj()

                #do something with the data
                print('#'*80)
                print('# message recieved at '+self.date_time_string())
                print('#'*80)
                #print(_metadata)
                self.pretty_print(_metadata, indent=1)

                #for key in _metadata.keys():
                #	print(key)

                # wait 5 seconds
                #time.sleep(5)
 
            except KeyboardInterrupt:
                self.stop_client()
                self.running = False
 
            except Exception as err:
                if self.verbosity > 0:
                    print(err)
                    self.stop_client()
                    self.running = False
 
    def date_time_string(self):
        return time.strftime('%Y-%m-%d_%H:%M:%S')

    def stop_client(self):
        self.socket.stop()

    def pretty_print(self, d, indent=0):
        for key, value in d.items():
            if isinstance(value, dict):
                print('\t' * indent + str(key)+ ' : ')
                self.pretty_print(value, indent+1)
            else:
                print('\t' * indent + str(key) + ' : '+str(value))
                #print('\t' * (indent+1) + str(value))

#####################################
## when run as a main
#####################################

if __name__ == '__main__':

    print('\n'*5)
    print('#'*80)

    # as descirbed here: 
    #     https://confluence.desy.de/display/FSP06/Online+Data+Processing
    host      = 'localhost'
    port      = 5556
    verbosity = 1

    listener  = zmq_listener(host, port, verbosity)

    print('#'*80)