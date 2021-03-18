"""
Module which provides Scheduler classes, which help the acquisition
system determine whether the instrument is ready to acquire, and if
there are any deadlines coming up that have to be avoided.
"""

import time
from threading import Thread
try:
    import tango
except:
    pass # makes building docs easier


class DummyScheduler(object):
    """
    Dummy base class to define the API.
    """
    @property
    def ready(self):
        """
        Whether or not the system is available now.
        """
        return self._ready()

    @property
    def limit(self):
        """
        Time left (in seconds) until the next deadline, None for no deadline.
        """
        return self._limit()

    def _ready(self):
        return True

    def _limit(self):
        return None


class DummyInjectionScheduler(DummyScheduler):
    """
    Dummy that does injection for one minute every five minutes.
    """
    def _ready(self):
        return time.localtime().tm_min % 5

    def _limit(self):
        whole_mins = 4 - (time.localtime().tm_min % 5)
        whole_secs = 60 - time.localtime().tm_sec
        return whole_mins * 60 + whole_secs

class TangoShutterChecker(Thread):
    """
    Helper class which asynchronously checks the status of a number of
    shutters and keeps their last statuses in a GIL-protected list,
    which can be accessed at any time.
    """
    def __init__(self, *shutter_devices):
        super().__init__()
        self.device_list = [tango.DeviceProxy(name) for name in shutter_devices]
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


class MaxivScheduler(DummyScheduler):
    """
    Scheduler to keep track of shutter status and the MAX IV injection system.

    NOTE: Using threaded status checkers here to avoid polling a large
    number of potentially slow shutter devices on a different control system.
    """
    def __init__(self, shutter_list):
        self.shutter_checker = TangoShutterChecker(*shutter_list)
        self.shutter_checker.start()
        self.injection_device = tango.DeviceProxy('g-v-csproxy-0:10000/R3-319S2/DIA/DCCT-01')
        self.countdown_device = tango.DeviceProxy('g-v-csproxy-0:10000/g/ctl/machinestatus')
        self.disabled = False

    def _ready(self):
        if self.disabled:
            return True
        else:
            shutters_ok = False not in self.shutter_checker.status_list
            try:
                injection_ok = (self.injection_device.lifetime > 0) # negative when refilling
            except:
                print("Couldn't reach the injection device %s, ignoring"%self.injection_device.name())
                injection_ok = True
            return (shutters_ok and injection_ok)

    def _limit(self):
        try:
            return self.countdown_device.r3topup
        except:
            return None
