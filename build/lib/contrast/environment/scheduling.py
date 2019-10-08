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


class MaxivInjectionScheduler(DummyScheduler):
    """
    Scheduler which keeps track of storage ring injections at MAX IV.
    Could also check the shutter status, so that closing the safety
    shutter pauses the scan!

    NOTE: It's probably best to write this as an asynchronous
    thread or process, because it might involve reading network
    attributes from the other side of the lab. It could do this at
    1 Hz or so, and the getters could just report on the latest
    value. That way scanning won't be slowed down.
    """
    pass
