try:
    import PyTango
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
        self.device = PyTango.DeviceProxy(sdm_device)

    @property
    def directory(self):
        return self.device.SamplePath

