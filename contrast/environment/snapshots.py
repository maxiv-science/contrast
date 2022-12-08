"""
Module which contains classes that gather information which
needs to be dumped to every scan.
"""


class EmptySnapshot(object):
    """
    Define the API.
    """
    def init(self):
        """
        some miniim of attributes
        """
        self.pre_scan = True
        self.post_scan = False

    def capture(self):
        """
        Returns a dict of label-value pairs.
        """
        return {}


class MotorSnapshot(EmptySnapshot):
    """
    Snapshot which consists of all motor values.
    """
    def capture(self):
        from contrast.motors import Motor
        dct = {}
        for m in Motor.getinstances():
            try:
                dct[m.name] = m.position()
            except:
                print('Could not take snapshot of motor %s' % m.name)
        return dct
