import os
import PyTango
import datetime
import time
import logging as log
log.basicConfig(filename='andor_log.txt',
                filemode='w+',
                format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                datefmt='%H:%M:%S',
                level=log.DEBUG)

if __name__ == '__main__':
    from contrast.detectors.Detector import Detector, SoftwareLiveDetector, TriggeredDetector, BurstDetector
    from contrast.environment import env
    from contrast.recorders.Hdf5Recorder import Link
else:
    from .Detector import Detector, SoftwareLiveDetector, TriggeredDetector, BurstDetector
    from ..environment import env
    from ..recorders.Hdf5Recorder import Link


class Andor3(Detector, SoftwareLiveDetector, BurstDetector):
    """
    Provides an interface to the Andor3 Zyla streaming manager,

    https://github.com/maxiv-science/andor-streamer

    Note: hw trigger not yet implemented.
    """

    def __init__(self, device='zyla/test/1', name=None):
        SoftwareLiveDetector.__init__(self)
        BurstDetector.__init__(self)
        Detector.__init__(self, name=name) # last so that initialize() can overwrite parent defaults
        self.proxy = PyTango.DeviceProxy(device)

    def initialize(self):
        pass

    def prepare(self, acqtime, dataid, n_starts):
        if self.busy():
            raise Exception('%s is busy!' % self.name)

        # saving and paths
        if dataid is None:
            # no saving
            self.saving_file = ''
            self.proxy.filename = ''
        else:
            # saving
            path = env.paths.directory
            fn = 'scan_%06d_%s.hdf5' % (dataid, self.name)
            self.saving_file = os.path.join(path, fn)
            if os.path.exists(self.saving_file):
                print('%s: this hdf5 file exists, I am raising an error now'%self.name)
                raise Exception('%s hdf5 file already exists' % self.name)
            self.proxy.filename = self.saving_file

        # arming and numbers of frames
        self.proxy.exposure_time = acqtime
        if self.burst_n == 1:
            self.proxy.trigger_mode = 'SOFTWARE'
            self.proxy.frame_count = n_starts
            self.proxy.start()
        else:
            self.proxy.trigger_mode = 'INTERNAL'
            self.proxy.frame_count = self.burst_n
        self.frames_expected = 0

    def arm(self):
        pass

    def start(self):
        if self.burst_n == 1:
            self.proxy.software_trigger()
            self.frames_expected += 1
        else:
            self.proxy.start()
            self.frames_expected = self.burst_n

    def stop(self):
        self.proxy.stop()

    def busy(self):
        st = self.proxy.State()
        if st in (PyTango.DevState.STANDBY, PyTango.DevState.ON):
            return False
        elif st == PyTango.DevState.RUNNING:
            if self.proxy.acquired_frames == self.frames_expected:
                return False
        return True

    def read(self):
        if self.saving_file == '':
            return None
        else:
            return Link(self.saving_file , 'entry/instrument/andor', universal=True)


class AndorSofti(Detector, BurstDetector):
    """
    Provides an interface to the Andor Zyla Tango DS at SoftiMAX
    """

    def __init__(self, device='B318A-EA01/dia/andor-zyla-01', name=None, frames_n=None):
        SoftwareLiveDetector.__init__(self)
        BurstDetector.__init__(self)
        Detector.__init__(self, name=name) # last so that initialize() can overwrite parent defaults
        self.proxy = PyTango.DeviceProxy(device)
        self.frames_n = frames_n
        self.file_path = env.paths.directory
        log.debug(f'AndorSofti __init__() call.')

    def initialize(self):
        pass

    def prepare(self, acqtime, dataid, n_starts):
        log.debug(f'Andor3 detector prepare() call with n_starts: {n_starts}.')
        if self.busy():
            raise Exception('%s is busy!' % self.name)

        self.saving_file = ''
        self.proxy.Stop()
        self.proxy.TriggerMode = 'SOFTWARE'

        if self.frames_n:
            self.burst_n = self.frames_n
        time_stamp = datetime.datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
        # saving and paths
        if dataid is None:
            self.dataid = None
            self.burst_n = 1
            self.proxy.nTriggers = 1
            self.saving_file = f'andor_ct_{time_stamp}.h5'
            andor_dest_name = os.path.join(self.file_path, self.saving_file)
            try:
                self.proxy.DestinationFilename = andor_dest_name
            except BaseException as err:
                raise Exception('Faild to set Andor DestinationFilename attr with the error: %s' % err)
        else:
            # saving
            self.dataid = dataid
            if self.burst_n == 1:
                # saving
                path = env.paths.directory
                fn = 'scan_%06d_%s.h5' % (dataid, self.name)
                self.saving_file = os.path.join(path, fn)
                if os.path.exists(self.saving_file):
                    print('%s: this h5 file exists, I am raising an error now'%self.name)
                    raise Exception('%s h5 file already exists' % self.name)
                self.proxy.DestinationFilename = self.saving_file
            else:
                try:
                    self.cam_path = os.path.join(self.file_path, f'scan_{self.dataid:06d}_{self.name}')
                    os.umask(0)
                    print(f'Attempting to create a new folder for the camera frames: {self.cam_path}')
                    os.makedirs(self.cam_path, mode=0o777)
                    print(f'Detector frames are written to: {self.cam_path}')
                    if os.path.exists(self.saving_file):
                        print('%s: this h5 file exists, I am raising an error now'%self.name)
                        raise Exception('%s h5 file already exists' % self.saving_file)
                    self.file_apndx = 0
                except BaseException as e:
                    print('prepare() exception: ', e)

        # arming and numbers of frames
        self.proxy.ExposureTime = acqtime
        if self.burst_n == 1:
            self.proxy.TriggerMode = 'SOFTWARE'
            self.proxy.nTriggers = n_starts

        self.frames_expected = 0

    def arm(self):
        log.debug(f'Andor3 detector arm() call.')
        while self.busy():
            time.sleep(0.01)
        if self.burst_n == 1:
            self.proxy.Arm()
            print('Armed in SOFTWARE trigger mode for a single trigger.')
            log.debug(f'Armed in SOFTWARE trigger mode for a single trigger.')
        elif self.burst_n > 1:
            log.debug(f'Armed in INTERNAL trigger mode, burst_n : {self.burst_n}')
            self.proxy.TriggerMode = 'INTERNAL'
            self.point_n_apndx = 0 
            self.proxy.nTriggers = self.burst_n

    def start(self):
        log.debug(f'Andor3 detector start() call.')
        while self.busy():
            print('Detector is busy at start().')
            log.debug(f'Andor3 detector start() call, but detector is busy. Andor3 detector state is {self.proxy.State()}')
        try:
            if self.burst_n == 1:
                if self.dataid:
                    self.frames_expected += 1
                else:
                    self.frames_expected += 1
                self.proxy.SoftwareTrigger()
            else:
                if self.dataid:
                    fn = 'scan_%06d_%s_%s.h5' % (self.dataid, self.name, self.file_apndx)
                    self.saving_file = os.path.join(self.cam_path, fn)
                    if os.path.exists(self.saving_file):
                        print('%s: this h5 file exists, I am raising an exception now..' % self.name)
                        log.debug(f'{self.name}: this h5 file exists, I am raising an exception now.')
                        raise Exception('%s h5 file already exists' % self.name)
                    self.proxy.DestinationFilename = self.saving_file
                    self.file_apndx += 1
                    self.frames_expected += self.burst_n
                    self.proxy.Arm()
                else:
                    print('No dataid')
        except AttributeError as e:
            print('start() exception: ', e)

    def stop(self):
        log.debug('Andor3 detector stop() call.')
        self.proxy.Stop()

    def busy(self):
        st = self.proxy.State()
        if st == PyTango.DevState.RUNNING and self.burst_n != 1:
            return True
        if st in (PyTango.DevState.STANDBY, PyTango.DevState.ON):
            return False
        elif st == PyTango.DevState.RUNNING:
            if self.proxy.nFramesAcquired == self.frames_expected:
                return False
        else:
            return True

    def read(self):
        log.debug('Andor3 detector read() call.')
        if self.saving_file == '':
            return None
        else:
            path, f_name = os.path.split(self.proxy.DestinationFilename)
            return Link(self.proxy.DestinationFilename, 'entry/instrument/zyla/data', universal=False)