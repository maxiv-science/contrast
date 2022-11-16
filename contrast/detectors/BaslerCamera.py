from .Detector import Detector
try:
    import PyTango
except ModuleNotFoundError:
    pass
import numpy as np
from taurus.core.util.codecs import CodecFactory


class BaslerCamera(Detector):
    """
    Interface to the tango device version of the Basla Cameras
    """
    def __init__(self, name=None, device=None):
        self.dev_name = device
        super().__init__(name=name)

    def initialize(self):
        self.dev = PyTango.DeviceProxy(self.dev_name) #camera tango device
        # for continuous acquisition, which will be doing anyway 
        # because of the viewer
        self.dev.nTriggers = 0 
        try:
            self.dev.Arm() # this will fail if the camera is running already
        except:
            print(f"[!] camera {self.name} is already running")
        self.cf = CodecFactory()

    def prepare(self, acqtime, dataid, n_starts):
        # the already set exposure time (basler viewer) will be used,
        # not the one in the scan command
        pass 

    def arm(self):
        pass

    def start(self):
        #self.dev.Measure()
        pass

    def stop(self):
        pass

    def busy(self):
        #return (self.dev.State() == PyTango.DevState.RUNNING)
        pass

    def read(self):
        ret = {}
        for i in range(3):
            # fetch the last image acquired by the microscope
            try:
                # for color images
                image_raw = self.dev.LastImageEncoded
                codec = self.cf.getCodec(image_raw[0])
                fmt, image_dec = codec.decode(image_raw)
                image = image_dec.astype(int)
            except:
                image = -1 * np.ones((1024,1280,3))
            # check if taking an image failed
            if not np.sum(image) < 0:
                break
            else:
                print("[!] failed frame, taking another one")
        ret['frames'] = np.array([image]) 
        return ret


