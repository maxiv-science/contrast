from contrast.scans.Scan import SoftwareScan
from contrast.motors import all_are_motors
from contrast.environment import macro, MacroSyntaxError, runCommand
from contrast.detectors import Detector, TriggeredDetector

@macro
class LoopScanDark(SoftwareScan):
    """
    A software scan with no motor movements. Number of exposures is
    <intervals> + 1, for consistency with ascan, dscan etc. ::

        loopscandark <intervals> <exp_time>
    """
    def __init__(self, intervals, exposuretime=1.0):
        super(LoopScanDark, self).__init__(float(exposuretime))
        self.intervals = intervals
        self.n_positions = intervals + 1
        self.motors = []

    def _before_scan(self):
        runCommand('fsclose')

    def _after_scan(self):
        runCommand('fsclose')

    def _generate_positions(self):
        # dummy positions with a non existent motor
        for i in range(self.intervals + 1):
            yield {'fake':i}