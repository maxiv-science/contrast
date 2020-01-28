import zmq
import sys
import time
import numpy

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

        if self.verbosity >= 1:
            print('\n'*5)
            print('#'*80)
            print('# started ZMQ listener:', 'tcp://'+host+':'+str(port))

            print('#'*80)

        self.run()

    def run(self):

        while self.running:
            try:
                # read the recieved message
                _metadata = self.socket.recv_pyobj()

                
                print('#'*80)
                print('# message recieved at '+self.date_time_string())
                print('#'*80)

                # just nicely print it out
                self.pretty_print(_metadata, indent=1)
 
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
            #elif isinstance(value, numpy.ndarray):
            #    print('\t' * indent + str(key) + ' : '+str(np.shape(value)))
            else:
                print('\t' * indent + str(key) + ' : '+str(value))

#####################################
## when run as a main
#####################################

if __name__ == '__main__':

    host      = 'localhost'
    port      = 5556
    verbosity = 1
    listener  = zmq_listener(host=host, port=port, verbosity=verbosity)

    print('#'*80)