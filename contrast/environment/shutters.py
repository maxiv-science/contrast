"""
Provides environment classes for interacting with shutters, as
often useful when scheduling. Kept in a separate module to avoid
dependencies on contrast.environment.scheduling.
"""

from threading import Thread
import time

class TangoShutterChecker(Thread):
    """
    Helper class which asynchronously checks the status of a number of
    shutters and keeps their last statuses in a GIL-protected list,
    which can be accessed at any time.
    """
    def __init__(self, *shutter_devices):
        super().__init__()
        import PyTango
        self.device_list = [PyTango.DeviceProxy(name) for name in shutter_devices]
        self.status_list = [True,] * len(shutter_devices)
        self.stopped = False

    def run(self):
        while not self.stopped:
            for i, dev in enumerate(self.device_list):
                try:
                    status = 'OPEN' in dev.status()
                except:
                    print('there was a problem reading shutter %s' % dev.name())
                    status = True
                self.status_list[i] = status
            time.sleep(3)

    def stop(self):
        self.stopped = True

