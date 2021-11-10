from .Detector import Detector, SoftwareLiveDetector, TriggeredDetector, BurstDetector
from ..environment import env
from ..environment import macro

import time
import numpy as np
try:
    import PyTango
except ModuleNotFoundError:
    pass
import os
from h5py import VirtualSource, VirtualLayout

class LimaDetector(Detector, SoftwareLiveDetector, TriggeredDetector, BurstDetector):
    """
    Lima base class.
    """
    EXT_TRG_MODE = "EXTERNAL_TRIGGER_MULTI"

    def __init__(self, name=None, lima_device=None, det_device=None):
        """
        Lima is sometimes very slow to finish writing data, which is why this
        gadget has a 'hybrid mode', where Lima is started only once, and sequential
        arm/start calls to this gadget only increment counters. The busy state
        is set based on Lima's last_image_acquired compared to these counters,
        and does not reflect the state of the Lima device.
        """
        self.lima_device_name = lima_device
        self.det_device_name = det_device
        self._hybrid_mode = False
        self.n_starts = -1
        Detector.__init__(self, name=name)
        SoftwareLiveDetector.__init__(self)
        TriggeredDetector.__init__(self)
        BurstDetector.__init__(self)

    def _safe_write(self, attr, val):
        ok = False
        while not ok:
            try:
                self.lima.write_attribute(attr, val)
                ok = True
            except PyTango.DevFailed as e:
                timeout = False
                for e_ in e.args:
                    if 'timeout' in e_.desc.lower():
                        print('*** Timeout when writing attribute %s on %s. Trying again...' % (attr, self.lima_device_name))
                        timeout = True
                if not timeout:
                    raise

    def _safe_read(self, attr):
        ok = False
        while not ok:
            try:
                result = self.lima.read_attribute(attr).value
                ok = True
            except PyTango.DevFailed as e:
                timeout = False
                for e_ in e.args:
                    if 'timeout' in e_.desc.lower():
                        print('*** Timeout when reading attribute %s on %s. Trying again...' % (attr, self.lima_device_name))
                        timeout = True
                if not timeout:
                    raise
        return result

    def _safe_call_command(self, cmd, params=None):
        """
        Noticed that lima calls tend to time out for no apparent
        reason, this works around it by trying again after timeouts
        but raising all other errors.
        """
        ok = False
        while not ok:
            try:
                self.lima.command_inout(cmd, params)
                ok = True
            except PyTango.DevFailed as e:
                timeout = False
                doublecall = False
                for e_ in e.args: 
                    if 'timeout' in e_.desc.lower():
                        print('*** Timeout during %s call to %s. Trying again...' % (cmd, self.lima_device_name))
                        timeout = True
                    if 'run prepareacq before starting' in e_.desc.lower():
                        print('*** StartAcq called twice on %s. Moving on...'%self.name)
                        doublecall = True
                        if not timeout:
                            ok = True
                if not timeout or doublecall:
                    raise

    def _initialize_det(self):
        """
        Initialize detector-specific properties such as cutoff energies
        and bias voltages. Can also be used for overriding Lima settings
        that were initialized by the base class.
        """
        pass

    @property
    def hybrid_mode(self):
        return self._hybrid_mode

    @hybrid_mode.setter
    def hybrid_mode(self, val):
        self._hybrid_mode = bool(val)
        self.arm_number = -1

    @property
    def energy(self):
        return -1

    @energy.setter
    def energy(self, val):
        pass

    def start_live(self, acqtime=1.0):
        self.hybrid_mode = False
        super(LimaDetector, self).start_live(acqtime)

    def initialize(self):
        self.lima = PyTango.DeviceProxy(self.lima_device_name)
        self.lima.set_timeout_millis(3000)
        self.det = PyTango.DeviceProxy(self.det_device_name)

        # Make sure the devices are reachable, or this will throw an error
        self.lima.state()
        self.det.state()
        
        self.lima.acq_trigger_mode = "INTERNAL_TRIGGER"
        self.lima.saving_mode = "AUTO_FRAME"
        self.lima.saving_frame_per_file = 1
        self.lima.acq_nb_frames = 1
        self.lima.saving_managed_mode = 'SOFTWARE'
        self.lima.saving_overwrite_policy = 'MULTISET'
        self.lima.saving_format = 'HDF5'
        self.lima.saving_suffix = '.hdf5'
        self.lima.saving_index_format = ''
        self.lima.latency_time = 0.0
        self._initialize_det()

        self.hybrid_mode = False
        self.arm_number = -1

    def make_virtual_layout(self):
        _, bytes, n, m = self.lima.image_sizes
        dtype = {1: np.uint8, 2: np.uint16, 4:np.uint32, 8:np.uint64}[int(bytes)]
        # we need to have relative paths in every virtual source object
        relfile = self.saving_filename

        if self.hw_trig:
            N = self.n_starts * self.burst_n * self.hw_trig_n
            layout = VirtualLayout(shape=(N, m, n), dtype=dtype)
            for i in range(self.n_starts):
                vsource = VirtualSource(relfile, self._hdf_path_base % i, shape=(self.hw_trig_n,m,n))
                layout[i*self.hw_trig_n:(i+1)*self.hw_trig_n] = vsource
        elif self.hybrid_mode:
            N = self.n_starts * self.burst_n
            layout = VirtualLayout(shape=(N, m, n), dtype=dtype)
            vsource = VirtualSource(relfile, self._hdf_path_base % 0, shape=(N, m, n))
            layout[:] = vsource
        else:
            N = self.n_starts * self.burst_n
            layout = VirtualLayout(shape=(N, m, n), dtype=dtype)
            for i in range(self.n_starts):
                layout[i*self.burst_n:(i+1)*self.burst_n] = VirtualSource(relfile, self._hdf_path_base % i, shape=(self.burst_n,m,n))
        return layout

    def prepare(self, acqtime, dataid, n_starts):
        BurstDetector.prepare(self, acqtime, dataid, n_starts)
        # get out of the fault caused by trigger timeout
        if (self._safe_read('acq_status') == 'Fault') and (self._safe_read('acq_status_fault_error') == 'No error'):
            self._safe_call_command('stopAcq')
            self._safe_call_command('prepareAcq')

        self.arm_number = -1
        self.n_starts = n_starts

        if self.busy():
            raise Exception('%s is busy!' % self.name)

        if dataid is None:
            # no saving
            self._safe_write('saving_mode', "MANUAL") # no saving
            self.saving_filename = None
        else:
            # saving
            self._safe_write('saving_directory', env.paths.directory)
            self._safe_write('saving_mode', "AUTO_FRAME")
            prefix = 'scan_%06d_%s' % (dataid, self.name)
            self._safe_write('saving_prefix', prefix)
            self.saving_filename = prefix + self._safe_read('saving_suffix')
            if os.path.exists(os.path.join(env.paths.directory, self.saving_filename)):
                print('%s hdf5 file already exists' % self.name)
                raise Exception('%s hdf5 file already exists' % self.name)

        if self.hw_trig:
            self._safe_write('acq_trigger_mode', self.EXT_TRG_MODE)
            self._safe_write('acq_nb_frames', self.hw_trig_n)
        else:
            self._safe_write('acq_trigger_mode', "INTERNAL_TRIGGER")
            self._safe_write('acq_nb_frames', self.burst_n)

        if self.hybrid_mode:
            if self.burst_n != 1:
                print('burst_n > 1 and hybrid mode makes no sense')
                raise Exception('burst_n > 1 and hybrid mode makes no sense')
            self._safe_write('acq_trigger_mode', self.EXT_TRG_MODE)
            self._safe_write('acq_nb_frames', n_starts)

        self._safe_write('acq_expo_time', self.acqtime)

        if self.hybrid_mode:
            time.sleep(.1)
            self._safe_call_command('prepareAcq')
            self._safe_call_command('startAcq')

        while self.busy():
            print(self.name, 'slept 5 ms while waiting for prepare')
            time.sleep(.005)

        # make a virtual layout to return instead of individual links
        # to individual datasets
        if self.saving_filename is not None:
            self.layout = self.make_virtual_layout()

    def arm(self):
        self.arm_number += 1
        if self.hybrid_mode:
            return
        if self.busy():
            raise Exception('%s is busy!' % self.name)
        self._safe_call_command('prepareAcq')
        while not self._safe_read('ready_for_next_acq'):
            time.sleep(.005)
        if self.hw_trig:
            self._safe_call_command('startAcq')

    def start(self):
        if self.hw_trig or self.hybrid_mode:
            return
        if self.busy():
            raise Exception('%s is busy!' % self.name)
        if self.hybrid_mode and self._safe_read('last_image_acquired') > -1:
            return
        else:
            self._safe_call_command('startAcq')

    def stop(self):
        self._safe_call_command('stopAcq')

    def busy(self):
        if self.hybrid_mode:
            if self.arm_number + 1 < self.n_starts:
                return self.arm_number > self._safe_read('last_image_acquired')
            elif not self._safe_read('ready_for_next_acq'):
                print('%s waiting for Lima...' % self.name)
                time.sleep(.5)
                return True
        else:
            return not self._safe_read('ready_for_next_acq')

    def read(self):
        if self.saving_filename is None:
            return None
        else:
            return {'frames': self.layout}

class LimaPilatus(LimaDetector):
    """
    Pilatus specific LimaDetector.
    """
    def __init__(self, *args, **kwargs):
        super(LimaPilatus, self).__init__(*args, **kwargs)
        self._hdf_path_base = 'entry_%04d/measurement/Pilatus/data'

    def _initialize_det(self):
        self.energy = 10.0
        self.burst_latency = 0.003

    @property
    def energy(self):
        return self.det.energy_threshold
        
    @energy.setter
    def energy(self, value):
        if value < 4.5 or value > 36:
            raise ValueError('Requested value is outside the Pilatus range of 4.5-36 keV')
        self.det.write_attribute('energy_threshold', value)

class LimaMerlin(LimaDetector):
    """
    Merlin specific LimaDetector.
    """
    def __init__(self, *args, **kwargs):
        super(LimaMerlin, self).__init__(*args, **kwargs)
        self._hdf_path_base = 'entry_%04d/measurement/Merlin/data'

    def _initialize_det(self):
        self.energy = 10.0
        self.det.write_attribute('gain', 'HGM')
        self.det.write_attribute('depth', 'BPP24')
        self.burst_latency = 0.002

    @property
    def energy(self):
        return self.det.operatingEnergy
        
    @energy.setter
    def energy(self, value):
        self.det.write_attribute('operatingEnergy', value)

    def prepare(self, *args, **kwargs):
        if self.hw_trig:
            self.det.write_attribute('triggerStartType', "RISING_EDGE_TTL")
        else:
            self.det.write_attribute('triggerStartType', "INTERNAL")
        BurstDetector.prepare(self, acqtime, dataid, n_starts)

class LimaAndor(LimaDetector):
    """
    Andor specific LimaDetector.
    """
    def __init__(self, *args, **kwargs):
        super(LimaAndor, self).__init__(*args, **kwargs)
        self._hdf_path_base = 'entry_%04d/measurement/Andor/data/array'

    def _initialize_det(self):
        self.lima.user_detector_name = 'Andor'

class LimaXspress3(LimaDetector):
    """
    Xspress3 specific LimaDetector.
    """
    EXT_TRG_MODE = "EXTERNAL_GATE"

    def __init__(self, *args, **kwargs):
        super(LimaXspress3, self).__init__(*args, **kwargs)
        self._hdf_path_base = 'entry_%04d/measurement/xspress3/data'

@macro
class Lima_hybrid_on(object):
    """
    Turn on 'hybrid triggering' for the specified Lima device,
    or for all Lima devices if nothing is specified.
    """
    VAL = True
    def __init__(self, *args):
        if args:
            self.dets = args
        else:
            self.dets = Detector.getinstances()

    def run(self):
        for d in self.dets:
            d.hybrid_mode = self.VAL

@macro
class Lima_hybrid_off(Lima_hybrid_on):
    """
    Turn on 'hybrid triggering' for the specified Lima device,
    or for all Lima devices if nothing is specified.
    """
    VAL = False

