"""
Module which provides Scheduler classes, which help the acquisition
system determine whether the instrument is ready to acquire, and if
there are any deadlines coming up that have to be avoided.
"""

import time

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


class MaxivScheduler(DummyScheduler):
    """
    Scheduler to keep track of shutter status at MAX IV, and which
    should also become capable of avoiding storage ring injections.

    NOTE: Using threaded status checkers here to avoid polling slow
    devices on the other side of the lab on every step.
    """
    def __init__(self, shutter_list):
        from .shutters import TangoShutterChecker
        self.shutter_checker = TangoShutterChecker(*shutter_list)
        self.shutter_checker.start()

    def _ready(self):
        return False not in self.shutter_checker.status_list

