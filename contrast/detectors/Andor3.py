import os
import PyTango
import datetime
import time
import logging as log
import signal
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


class CameraBusyException(Exception):
    pass


class AndorSofti(Detector, BurstDetector):
    """
    Provides an interface to the Andor Zyla Tango DS at SoftiMAX
    """

    def __init__(self, device='B318A-EA01/dia/andor-zyla-01', name=None, shutter=None, frames_n=None):
        BurstDetector.__init__(self)
        Detector.__init__(self, name=name) # last so that initialize() can overwrite parent defaults
        self.proxy = PyTango.DeviceProxy(device)
        self.frames_n = frames_n
        self.frames_expected = 0
        self.file_path = env.paths.directory
        self.shutter = shutter
        log.debug(f'AndorSofti __init__() call.')
        signal.signal(signal.SIGALRM, self._busy_handler)

    def initialize(self):
        log.debug(f'Andor3 detector initialize() call.')

    def prepare(self, acqtime, dataid, n_starts):
        if n_starts:
            self.n_starts = n_starts
            log.debug(f'Andor3 detector prepare() call with n_starts: {n_starts}.')
        if self.busy():
            raise Exception('%s is busy!' % self.name)

        self.saving_file = ''
        self.proxy.Stop()

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
                self.proxy.nTriggers = 1
                # saving
                path = env.paths.directory
                fn = 'scan_%06d_%s.h5' % (dataid, self.name)
                self.saving_file = os.path.join(path, fn)
                if os.path.exists(self.saving_file):
                    print('%s: this h5 file exists, I am raising an error now'%self.name)
                    raise Exception('%s h5 file already exists' % self.name)
                self.proxy.DestinationFilename = self.saving_file
            elif self.burst_n > 1:
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
            self.proxy.nTriggers = 1
            print('Preparation is done for a single software trigger, self.proxy.nTriggers: ', self.proxy.nTriggers)
        elif self.burst_n > 1:
            self.proxy.TriggerMode = 'INTERNAL'
            self.proxy.nTriggers = self.burst_n
            print('Detector preaparation done.')

    def arm(self):
        log.debug(f'Andor3 detector arm() call.')
        try:
            while self.busy():
                time.sleep(0.01)
        except CameraBusyException as e:
            print('Incrementing the self.frames_expected.')
            self.frames_expected += 1

        if self.burst_n == 1:
            self.frames_expected = 1
            self.proxy.Arm()
            print('Armed in SOFTWARE trigger mode for a single trigger.')
            log.debug(f'Armed in SOFTWARE trigger mode for a single trigger.')
        elif self.burst_n > 1:
            log.debug(f'Prepearing to measure in INTERNAL trigger mode, burst_n: {self.burst_n}')
            self.point_n_apndx = 0 
            self.frames_expected = self.burst_n

    def start(self):
        log.debug(f'Andor3 detector start() call.')
        signal.alarm(60)

        try:
            if self.shutter:
                self.shutter.Open()
        except BaseException as e:
            print('Problem openning the shutter')

        try:
            if self.burst_n == 1:
                print('Before the software trig.')
                self.proxy.SoftwareTrigger()
            elif self.burst_n > 1:
                fn = 'scan_%06d_%s_%s.h5' % (self.dataid, self.name, self.file_apndx)
                self.saving_file = os.path.join(self.cam_path, fn)
                if os.path.exists(self.saving_file):
                    print('%s: this h5 file exists, I am raising an exception now..' % self.name)
                    log.debug(f'{self.name}: this h5 file exists, I am raising an exception now.')
                    raise Exception('%s h5 file already exists' % self.name)
                self.proxy.DestinationFilename = self.saving_file
                self.file_apndx += 1
                log.debug(f'Andor3 detector arming from start() call.')
                self.proxy.Arm()
        except AttributeError as e:
            print('start() AttributeError exception: ', e)
        except CameraBusyException as e:
            print('Incrementing the self.frames_expected.')
            self.frames_expected += 1
        except BaseException as e:
            print('BaseException in detector start()', e)
            print('self.frames_expected: ', self.frames_expected)
            print('self.burst_n: ', self.burst_n)
            log.debug(f'BaseException in detector start(): {e}')
            log.debug(f'self.frames_expected: {self.frames_expected}')
            log.debug(f'self.burst_n: {self.burst_n}')
            log.debug(f'self.proxy.nFramesAcquired: {self.proxy.nFramesAcquired}')
            log.debug(f'self.proxy.State(): {self.proxy.State()}')

    def stop(self):
        log.debug('Andor3 detector stop() call.')
        self.proxy.Stop()
        try:
            if self.shutter:
                self.shutter.Close()
        except BaseException as e:
            print('Problem closing the shutter')
        signal.alarm(0)

    def _busy_handler(self, signum, frame):
        print('The camera is busy for too long, raising an exception!')
        raise CameraBusyException('Camera is busy for too long, possibly missed frame!')

    def busy(self):
        st = self.proxy.State()
        if self.frames_expected > 0 and self.proxy.nFramesAcquired != self.frames_expected:
            return True
        elif st in (PyTango.DevState.STANDBY, PyTango.DevState.ON):
            return False
        elif self.burst_n != 1 and st == PyTango.DevState.RUNNING:
            return True
        elif st == PyTango.DevState.RUNNING:
            if self.proxy.nFramesAcquired == self.frames_expected:
                return False
        else:
            return True

    def read(self):
        try:
            if self.shutter:
                self.shutter.Close()
        except BaseException as e:
            print('Problem closing the shutter')

        log.debug('Andor3 detector read() call.')
        if self.saving_file == '':
            return None
        else:
            path, f_name = os.path.split(self.proxy.DestinationFilename)
            return Link(self.proxy.DestinationFilename, 'entry/instrument/zyla/data', universal=False)