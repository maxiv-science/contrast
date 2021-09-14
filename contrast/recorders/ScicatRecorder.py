from . import Recorder
from scifish import SciFish
from ..detectors import Detector

class ScicatRecorder(Recorder):
    """
    Recorder which submits acquisition info to the SciCat database via a helper library.
    """
    def __init__(self, name=None):
        Recorder.__init__(self, name=name)

    def act_on_header(self, dct):
        """
        Give SciCat all the info for this scan.
        """
        self.entry = SciFish()
        self.entry.start_scan()
        self.entry.scicat_data.datasetName = dct['scannr']
        self.entry.scicat_data.scanID = dct['scannr']
        self.entry.scicat_data.title = dct['description']
        #self.entry.scicat_data.sampleId = ""
        #self.entry.scicat_data.dataFormat = ""
        #self.entry.scicat_data.files = []
        #self.entry.scicat_data.sourceFolder = "" # default from sdm
        #self.entry.scicat_data.description = ""
        det_group = Detector.get_active()
        self.entry.scicat_data.detectors = sorted([d.name for d in det_group])

    def act_on_data(self, dct):
        """
        Only scan-level information is sent.
        """
        pass

    def act_on_footer(self, dct):
        """
        Tell SciCat that the scan is done
        """
        self.entry.end_scan()

