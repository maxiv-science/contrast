try:
    from tango import DeviceProxy, DevError
except ModuleNotFoundError:
    pass


class PathFixer(object):
    """
    Basic pathfixer which takes a path manually.
    """
    def __init__(self):
        self.directory = None


class SdmPathFixer(object):
    """
    MAX IV pathfixer which takes a path from a Tango device.
    """
    def __init__(self, sdm_device):
        self.device = DeviceProxy(sdm_device)
        self.TRIALS = 10
        self.cache = None

    @property
    def directory(self):
        for trial in range(self.TRIALS):
            try:
                val = self.device.SamplePath
                self.cache = val
                return val
            except DevError:
                print('Failed in getting SDM path from Tango. Trying again...')
        print('Failed %u times, using cached value: %s'
              % (self.TRIALS, self.cache))
        return self.cache
