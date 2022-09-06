import os
import datetime
import time
from tango import DeviceProxy, DevState

from .Detector import Detector, SoftwareLiveDetector, TriggeredDetector, BurstDetector
from ..environment import env
from ..recorders.Hdf5Recorder import Link


class DhyanaAndor(Detector, BurstDetector):
    """
    Provides an interface to the Dhyana and Andor3 Tango devices
    as used at SoftiMAX.

    see here for MAX IV Tango devices (and complicated daq pipelines)
    https://gitlab.maxiv.lu.se/kits-maxiv/dhyana/dev-maxiv-dhyana
    https://gitlab.maxiv.lu.se/kits-maxiv/andor3/dev-maxiv-andor3
    """

    def __init__(self, device='B318A-EA01/dia/dhyana', name=None, hdf_name=None, debug=False):
        BurstDetector.__init__(self)
        Detector.__init__(self, name=name) # last so that initialize() can overwrite parent defaults
        self.proxy = DeviceProxy(device)
        self.hdf_name = name if hdf_name is None else hdf_name
        self.do_debug = debug
        self.frames_expected = 0

    def debug(self, *msgs):
        if self.do_debug:
            print('***', *msgs)

    def initialize(self):
        pass

    def prepare(self, acqtime, dataid, n_starts):
        if self.busy():
            raise Exception('%s is busy!' % self.name)

        self.saving_file = ''
        self.stop()


        # saving and paths
        if dataid is None:
            # This Tango DS insists on writing files, so make up a name
            self.dataid = None
            time_stamp = datetime.datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
            fn = os.path.join(env.paths.directory, f'{self.name}_ct_{time_stamp}.h5')
            try:
                self.proxy.DestinationFilename = fn
            except BaseException as err:
                raise Exception('Failed to set %s DestinationFilename attr with the error: %s' % (self.name, err))
        else:
            self.dataid = dataid  # needed for burst mode later
            if self.burst_n == 1:
                # saving
                path = env.paths.directory
                fn = 'scan_%06d_%s.h5' % (dataid, self.name)
                self.saving_file = os.path.join(path, fn)
                if os.path.exists(self.saving_file):
                    self.debug('%s: this h5 file exists, I am raising an error now'%self.name)
                    raise Exception('%s h5 file already exists' % self.name)
                self.proxy.DestinationFilename = self.saving_file
            elif self.burst_n > 1:
                # set up a folder for separate burst files, exact path filled in start()
                self.cam_path = os.path.join(env.paths.directory,
                                    f'scan_{self.dataid:06d}_{self.name}')
                os.umask(0)
                os.makedirs(self.cam_path, mode=0o777)

        if self.burst_n > 1:
            self.burst_indx = 0

        # arming and numbers of frames
        self.proxy.ExposureTime = acqtime
        if int(self.burst_n) == 1:
            self.proxy.TriggerMode = 'SOFTWARE'
            self.debug('device trig mode is now %s' % self.proxy.TriggerMode)
            self.proxy.nTriggers = n_starts
            self.proxy.Arm()
            while not self.proxy.State() == DevState.RUNNING:
                time.sleep(.01)
            self.frames_expected = 0
        elif self.burst_n > 1:
            self.proxy.TriggerMode = 'INTERNAL'
            self.proxy.nTriggers = self.burst_n
            self.frames_expected = self.burst_n

    def arm(self):
        pass            

    def start(self):
        if self.burst_n == 1:
            self.debug('softtrig')
            self.proxy.SoftwareTrigger()
            self.frames_expected += 1
        elif self.burst_n > 1:
            if self.dataid is not None:
                fn = 'scan_%06d_%s_%s.h5' % (self.dataid, self.name, self.burst_indx)
                fn = os.path.join(self.cam_path, fn)
                if os.path.exists(fn):
                    self.debug('%s: this h5 file exists, I am raising an exception now..' % self.name)
                    raise Exception('%s h5 file already exists' % self.name)
                self.proxy.DestinationFilename = fn
                self.burst_indx += 1
            self.proxy.Arm()

    def stop(self):
        self.proxy.Stop()

    def busy(self):
        st = self.proxy.State()
        self.debug('busy():', st, self.proxy.nFramesAcquired)
        if st == DevState.MOVING:
            am_busy = True
        elif st in (DevState.STANDBY, DevState.ON):
            am_busy = False
        elif st == DevState.RUNNING:
            if self.burst_n > 1:
                # in burst mode the tango state actually reflects whether the camera is busy
                am_busy = True
            else:
                # otherwise, you have to look at frame numbers
                self.debug('checking numbers, %u and %u' % (self.frames_expected, self.proxy.nFramesAcquired))
                am_busy = (self.frames_expected > self.proxy.nFramesAcquired)
        else:
            # FAULT etc
            am_busy = True
        self.debug('concluded', am_busy)
        return am_busy

    def read(self):
        if self.dataid:
            path, f_name = os.path.split(self.proxy.DestinationFilename)
            return Link(self.proxy.DestinationFilename, 'entry/instrument/%s/data' % self.hdf_name, universal=(self.burst_n==1))
        else:
            return None

