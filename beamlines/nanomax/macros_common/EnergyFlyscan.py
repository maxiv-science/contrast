from contrast.scans.Scan import SoftwareScan
from contrast.motors import all_are_motors
from contrast.environment import macro, MacroSyntaxError, runCommand
from contrast.detectors import Detector, TriggeredDetector, PandaBox_PCAP
import time
import tango

@macro
class EnergyFlyscan(SoftwareScan):

    PCAP = None
    energy_motor = None
    ivu_gap_motor = None
    # Pandabox for coordinating the energyflyscan
    energyflyscan_panda = None
    # Panda for re-distributing the triggers to detectors
    trigger_distribution_panda = None

    def __init__(self, start_energy, end_energy, intervals, exposure_time, latency = None, use_id = True):
        self.start_energy = start_energy
        self.end_energy = end_energy
        self.intervals = intervals
        self.exposuretime = exposure_time
        self.use_id = use_id

        # init Software Scan
        super().__init__(self.exposuretime)

        self.n_positions = self.intervals + 1

        # check if PCAP for energy capturing is set
        if self.PCAP is None:
            raise Exception('Set EnergyFlyscan.PCAP to the Pandabox_PCAP detector')
        # elif not isinstance(self.PCAP, PandaBoxPCAP):
        #     raise Exception(' EnergyFlyscan.PCAP is not not a Pandabox_PCAP detector')

        # check if energy motor is configured
        if self.energy_motor is None:
            raise Exception('Set EnergyFlyscan.energy_motor to your energy motor')
        # check ic ivu_gap motor is configured
        if self.ivu_gap_motor is None:
            raise Exception('Set EnergyFlyscan.ivu_gap_motor to your ivu_gap motor')

        # check if the pandabox for energy fly scanning is configured
        if self.energyflyscan_panda is None:
            raise Exception('Set EnergyFlyscan.energyflyscan_panda to your energyflyscanning pandabox')

        # check is a trigger distribution panda box is configured
        if self.trigger_distribution_panda is None:
            raise Exception('Set EnergyFlyscan.trigger_distribution_panda to your trigger distributing pandabox')
        #
        # self.motors.append(self.energy_motor)
        # self.motors.append(self.ivu_gap_motor)

        # init the other required tango servers
        # this is hard-coded for now
        # TODO: make this configurable
        self.panda = tango.DeviceProxy("B303A-A100380CAB03/TIM/PANDA-01")
        # PCAP = "b303a-a100380cab03/dia/panda-01"
        self.bragg = tango.DeviceProxy("bragg")
        self.z1 = tango.DeviceProxy("tango://g-v-csproxy-0:10303/r3-303l/id/idivu-01_mc401")
        self.energy = tango.DeviceProxy("energy")
        self.energy_corr = tango.DeviceProxy("energy_corr")
        self.ivu = tango.DeviceProxy("tango://g-v-csproxy-0:10303/r3-303l/id/idivu-01_gap")
        self.ivu.set_source(tango.DevSource.DEV)
        self.mono_traj = tango.DeviceProxy("mono_energy_traj")
        self.mono_traj.set_source(tango.DevSource.DEV)
        self.id_traj = tango.DeviceProxy("tango://g-v-csproxy-0:10303/r3-303l/id/idivu-01_energy_traj")
        self.id_traj.set_source(tango.DevSource.DEV)
        self.id_traj_ctrl = tango.DeviceProxy("tango://g-v-csproxy-0:10303/r3-303l/id/idivu-01_energy_traj_ctrl")
        self.id_traj_ctrl.set_source(tango.DevSource.DEV)

        # check if specified latency is compatible with active detectors
        min_latency = 0
        for d in Detector.get_active():
            if isinstance(d, TriggeredDetector):
                if d.hw_trig_min_latency > min_latency:
                    min_latency = d.hw_trig_min_latency

        # use user specified latency if given as keyword, otherwise use min_latency
        if latency is None:
            self.latency = min_latency
            print(f"Latency set to {self.latency:g} s, based on active detectors")
        else:
            if latency < min_latency:
                raise ValueError(f"The specified latency {latency:g} s is shorter than the required hardware latency {min_latency:g} s of the active detector(s). Detector(s) will miss triggers.")
            self.latency = latency
            print(f"Latency set to {self.latency:g} s by user.")
 
        # activate energy fly scanning pandabox
        self.energyflyscan_panda.active = True

        self.flyscan = True
        self.trigger_distribution_panda.set_trigger_mode('external')


    def _before_scan(self):
        super()._before_scan()
        self._check_pandabox_schema()
        self._configure_pandabox()

    # def _before_move(self):
    #     self._sync_ID_bragg()
    
    def run(self):
        try:
            # more things to do here #
            super().run()
        except:
            self._cleanup()
            raise

        self._cleanup()

    def _cleanup(self):
        self.trigger_distribution_panda.set_trigger_mode('internal')
        # deactivate energy fly scanning pandabox
        self.energyflyscan_panda.active = False

        # # reset the velocity of the ivu trajectory and the energy/bragg trajectory to the maxi,um allowed velocity
        # print("### before cleanup ###")
        # print(f"{self.mono_traj.Velocity = } {self.mono_traj.Acceleration = }")
        # print(f"{self.id_traj.Velocity = } {self.id_traj.Acceleration = }")
        # self.id_traj.Velocity = self.id_traj.MaxVelocity
        # self.mono_traj.Velocity = self.mono_traj.MaxVelocity
        # print("### after cleanup ###")
        # print(f"{self.mono_traj.Velocity = } {self.mono_traj.Acceleration = }")
        # print(f"{self.id_traj.Velocity = } {self.id_traj.Acceleration = }")

    def _check_pandabox_schema(self):
        # check the schema
        # the command bellow returns:
        # False - schemas are different
        # True - schemas are good
        if self.panda.SchemaCheck():
            print("Panda runtime schema is loaded as expected!")
        else:
            # if schema_flag is False means that the rubtime schema id different than
            # expected, so will run the SchemaLoad command to sync it
            self.panda.SchemaLoad()
            # will assert it loaded correctly, maybe need to add a sleep after command above
            assert self.panda.SchemaCheck(), "Schema Load failed"

    def _configure_pandabox(self):
        self.panda.nPoints = self.n_positions
        self.panda.ExposureTime = self.exposuretime
        self.panda.LatencyTime = self.latency
        self.panda.EncInUse = True  # this should be always True if running a cont energy scan
        (energy_raw, *_) = self.energy_corr.CalcAllPhysical([self.start_energy])  # START energy in eV dont use pre-start
        (bragg_value, *_) = self.energy.CalcAllPhysical([energy_raw])
        bragg_encoder_value = (
            (bragg_value + self.bragg.Offset) * self.bragg.Step_per_unit * self.bragg.Sign
        )
        self.panda.PCOMPReference = bragg_encoder_value
        print("Panda configured for given parameters")

    def _sync_ID_bragg(self):
        # make sure ID and bragg are not moving before calling the commands bellow
        # Sync bragg motor
        assert self.bragg.State() not in [tango.DevState.MOVING], "bragg motor is moving, stop it before sync panda encoder"
        self.panda.SyncBragg(self.bragg.EncTgtEnc)
        # Sync IVU Z1 motor - note this must access accelerator control system
        if self.use_id:
            assert self.z1.State() not in [tango.DevState.MOVING], "IVU is moving, stop it before sync panda encoder"
        self.panda.SyncIVU(self.z1.EncAbsEnc)
        print("Panda encoder is synced with icepap encoders")

    def _generate_positions(self):
        '''
        use _generate_positions method to calculate the start positions of energy motor and ivu_gap motor
        '''
        positions = {'none': 0}
        yield positions

    def _before_move(self):
        ### calculations section start
        # calculate velocity
        # here you can add check for allowed velocities if needed
        velocity = abs(self.end_energy - self.start_energy) / ((self.intervals-1) * (self.exposuretime + self.latency))
        print(f"scan velocity is {velocity} in eV/s")

        # calculate the acceleration time and compensation for trapezoidal profile
        # set the scanned acc time to the slowest system involved
        mono_acc = self.mono_traj.Acceleration
        id_acc = self.id_traj.Acceleration
        # set acceleration time to slowest
        # self.mono_traj.Acceleration = 1 # max_acc
        # self.id_traj.Acceleration = 1 # max_acc
        #self.mono_traj.Acceleration = max_acc
        #self.id_traj.Acceleration = max_acc
        max_acc = max(mono_acc, id_acc)
        self.acct = max_acc
        energy_compensation = velocity * max_acc / 2
        print(f"Energy compensation for trapezoidal profile if {energy_compensation} eV")
        print(
            f"Max acceleration time is {max_acc} seconds, both systems were configured to match that"
        )

        # calculate pre-start and post-final position for energy compensation
        # check direction of scan for right compensation
        if self.end_energy > self.start_energy:
            pre_start = self.start_energy - energy_compensation
            post_final = self.end_energy + energy_compensation
        else:
            pre_start = self.start_energy + energy_compensation
            post_final = self.end_energy - energy_compensation
        self.post_final = post_final
        print(f"Pre-start position at {pre_start} eV")
        print(f"Post-final position at {post_final} eV")
        self.energy_compensation = energy_compensation
        self.scan_velocity = velocity
        self.pre_start = pre_start
        ### calculations section end
        # check IVU harmonic range for given scan parameters
        if self.use_id:
            ranges = self.id_traj_ctrl.get_property("EnergyRanges")["EnergyRanges"]
            # note for the step bellow you should use pre-start and post-final to make sure the motion
            # space fits in the active trajectory range
            s = min(pre_start, post_final)  # lower energy independent of scan direction
            f = max(pre_start, post_final)  # higher energy independent of scan direction
            harmonic = None
            for r in ranges:
                rr = r.split(":")[1].split(", ")
                (r_min, r_max) = rr
                if s > float(r_min) and f < float(r_max):
                    harmonic = int(r.split(":")[0])
                    print(
                        f"IVU harmonic is {harmonic}, Energy range for this harmonic is {r_min} and {r_max}"
                    )
            assert (
                harmonic is not None
            ), f"Failed to find IVU harmonic for given scan energy or it crosses harmonics. ID harmonic table:\n{ranges}"
            self.id_traj.Harmonic = harmonic
            time.sleep(1)
            while self.id_traj.State() in [tango.DevState.MOVING]:
                time.sleep(1)
            print("IVU harmonic configured")
        
        # move energy to pre-start energy
        self.energy_motor.move(pre_start)
        # TODO move ID to pre_start gap
        while self.energy_motor.busy():
            time.sleep(0.1)
        
        self._sync_ID_bragg()
         # sync trajectory motor and set speed to maximum
        # clean min max trajectory range if needed
        self.mono_traj.MoveOntoTrajectoryAt = self.mono_traj.NearestTrajectoryPosition
        if self.use_id:
            self.id_traj.MoveOntoTrajectoryAt = self.id_traj.NearestTrajectoryPosition
        # wait for trajectory sync to finish
        time.sleep(1)
        while self.mono_traj.State() or self.id_traj.State() in [tango.DevState.MOVING]:
            print("moving mono onto trajectory")
            time.sleep(0.1)
        if self.use_id:
            while self.id_traj.State() in [tango.DevState.MOVING]:
                print("moving id onto trajectory")
                time.sleep(0.1)

        assert self.mono_traj.State() in [
            tango.DevState.ON
        ], f"Mono trajectory sync failed {self.mono_traj.State()} {self.mono_traj.Status()}"
        if self.use_id:
            assert self.id_traj.State() in [
                tango.DevState.ON
            ], f"ID trajectory sync failed {self.id_traj.State()} {self.id_traj.Status()}"
        print("ID and mono trajectories are synced")
        
        # # check and set the min and max activy trajectory ranges
        # # in order to accomodate higher speeds if needed
        # padding = 200
        # self.id_traj.MinTrajRange = s - padding
        # self.id_traj.MaxTrajRange = f + padding
        # self.mono_traj.MinTrajRange = s - padding
        # self.mono_traj.MaxTrajRange = f + padding
        # print(f"Energy range set to [{s-padding:.3f}, {f+padding:.3f}] eV")

        # check if scan velocity is allowed for that giving trajectory
        assert (
            velocity <= self.mono_traj.MaxVelocity
        ), f"requested {velocity=} is above mono max speed {self.mono_traj.MaxVelocity}"
        if self.use_id:
            assert (
                velocity <= self.id_traj.MaxVelocity
            ), f"requested {velocity=} is above id max speed {self.id_traj.MaxVelocity}"
        # set velocity
        self.mono_traj.Velocity = velocity
        if self.use_id:
            self.id_traj.Velocity = velocity
        print(f"Trajectories velocities were configured for {velocity} eV/s")
        print(f"{self.mono_traj.Velocity = } {self.mono_traj.Acceleration = }")
        print(f"{self.id_traj.Velocity = } {self.id_traj.Acceleration = }")
        print(f"{self.mono_traj.MaxVelocity = }  {self.id_traj.MaxVelocity = }")

         # move to pre-start position using trajectory after synced
        print(f"About to move the motors to pre-start position at {pre_start} eV")
        # time.sleep(0.5)
        print(f"{self.mono_traj.State() = } {self.id_traj.State() = }")
        print(f"{self.mono_traj.Status() = }\n{self.id_traj.Status() = }")
        self.mono_traj.Position = pre_start
        if self.use_id:
            self.id_traj.Position = pre_start
        # wait for motion to finish
        time.sleep(0.1)
        while self.mono_traj.State() or self.id_traj.State() in [tango.DevState.MOVING]:
            time.sleep(0.1)
            if self.use_id:
                print(f"ID current position {self.id_traj.Position} eV", end="\r")
            print(f"Mono current position: {self.mono_traj.Position} eV", end="\r")  

    def _before_arm(self):
        self.panda.Arm()

    def _before_start(self):
        self.panda.Start()
        print("Panda started")
        # Start your motion here, dont forget to check direction and compensate for trapezoidal profile
        print("Starting motion to:", self.post_final)
        self.mono_traj.Position = self.post_final
        if self.use_id:
            self.id_traj.Position = self.post_final


@macro
class EnergyFlyscanAcct(EnergyFlyscan):

    def __init__(self, start_energy, end_energy, intervals, exposure_time, latency = None, use_id = True, acct = None):
        self.acct = acct
        self.pcapds = tango.DeviceProxy("b303a-a100380cab03/dia/panda-01")    
        # init standard EnergyFlyScan
        super().__init__(start_energy, end_energy, intervals, exposure_time, latency, use_id)

    def _configure_pandabox(self):
        # acct could be configured in more suitable method
        if self.acct != None:
            self.mono_traj.Acceleration = self.acct # max_acc
            self.id_traj.Acceleration = self.acct# max_acc
        super()._configure_pandabox()
        # self.pcapds.nTriggers=self.panda.nPoints

    def _before_start(self):
        #print("###before start")
        #print('###', self.panda.nPoints,  self.panda.EncInUse, self.panda.PCOMPReference, self.pcapds.nTriggers)
        super()._before_start()
        # self.pcapds.nTriggers=self.panda.nPoints

@macro
class EnergyFlyscanScp(EnergyFlyscan):

    def __init__(self, start_energy, end_energy, intervals, exposure_time, latency = None, use_id = True, acct = None):
        self.acct = acct
        # init standard EnergyFlyScan
        super().__init__(start_energy, end_energy, intervals, exposure_time, latency, use_id)

    def _configure_pandabox(self):
        # acct could be configured in more suitable method
        if self.acct != None:
            self.mono_traj.Acceleration = self.acct # max_acc
            self.id_traj.Acceleration = self.acct# max_acc
        ### calculations section start (copy of EnergyFlyscan before_move calculations)
        # calculate velocity
        # here you can add check for allowed velocities if needed
        velocity = abs(self.end_energy - self.start_energy) / ((self.intervals-1) * (self.exposuretime + self.latency))
        print(f"scan velocity is {velocity} in eV/s")

        # calculate the acceleration time and compensation for trapezoidal profile
        # set the scanned acc time to the slowest system involved
        mono_acc = self.mono_traj.Acceleration
        id_acc = self.id_traj.Acceleration
        # set acceleration time to slowest
        #self.mono_traj.Acceleration = max_acc
        #self.id_traj.Acceleration = max_acc
        max_acc = max(mono_acc, id_acc)
        self.acct = max_acc
        energy_compensation = velocity * max_acc / 2
        print(f"Energy compensation for trapezoidal profile if {energy_compensation} eV")
        print(
            f"Max acceleration time is {max_acc} seconds, both systems were configured to match that"
        )

        # calculate pre-start and post-final position for energy compensation
        # check direction of scan for right compensation
        if self.end_energy > self.start_energy:
            pre_start = self.start_energy - energy_compensation
            post_final = self.end_energy + energy_compensation
        else:
            pre_start = self.start_energy + energy_compensation
            post_final = self.end_energy - energy_compensation
        self.post_final = post_final
        print(f"Pre-start position at {pre_start} eV")
        print(f"Post-final position at {post_final} eV")
        self.energy_compensation = energy_compensation
        self.scan_velocity = velocity
        self.pre_start = pre_start
        ### calculations section end

        self.pcapds = tango.DeviceProxy("b303a-a100380cab03/dia/panda-01")    
        self.acct_positions = self.acct / (self.latency + self.exposuretime)
        self.additional_positions = int(1.1 * (self.acct_positions * 2))
        # Start with 10% extra
        self.panda.nPoints = self.n_positions + self.additional_positions
        self.panda.ExposureTime = self.exposuretime
        self.panda.LatencyTime = self.latency
        self.panda.EncInUse = (
            True  # this should be always True if running a cont energy scan
        )
        self.pcapds.nTriggers=self.panda.nPoints
        (energy_raw, *_) = self.energy_corr.CalcAllPhysical(
            # [self.start_energy]
            [self.pre_start]
        )  # START energy in eV dont use pre-start
        (bragg_value, *_) = self.energy.CalcAllPhysical([energy_raw])
        bragg_encoder_value = (
            (bragg_value + self.bragg.Offset)
            * self.bragg.Step_per_unit
            * self.bragg.Sign
        )
        self.panda.PCOMPReference = bragg_encoder_value - 100
        # print('###', self.panda.nPoints,  self.panda.EncInUse, self.panda.PCOMPReference, bragg_encoder_value, self.pcapds.nTriggers)
        print("Panda configured for given parameters")


    def _before_start(self):
        #print("###before start")
        self.pcapds.nTriggers=self.panda.nPoints
        #print('###', self.panda.nPoints,  self.panda.EncInUse, self.panda.PCOMPReference, self.pcapds.nTriggers)
        self.panda.Start()
        print("Panda started")
        # Start your motion here, dont forget to check direction and compensate for trapezoidal profile
        print("Starting motion from:" , self.mono_traj.Position, "  to:", self.post_final, ' pcomp:', self.panda.PCOMPReference, ' bragg enc:', self.bragg.enctgtenc )
        self.mono_traj.Position = self.post_final
        if self.use_id:
            self.id_traj.Position = self.post_final
