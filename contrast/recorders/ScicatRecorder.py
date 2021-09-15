from . import Recorder
from scifish import SciFish
from ..detectors import Detector

class ScicatRecorder(Recorder):
    """
    Recorder which submits acquisition info to the SciCat database via a helper library.
    """
    def __init__(self, name=None, verbose=False):
        Recorder.__init__(self, name=name)
        self.verbose = verbose

    def act_on_header(self, dct):
        """
        Give SciCat all the info for this scan. Enters the whole snapshot.
        """
        self.entry = SciFish()
        self.entry.start_scan()
        self.entry.scicat_data.datasetName = dct['scannr']
        self.entry.scicat_data.sampleId = dct['scannr']
        #self.entry.scicat_data.dataFormat = ""
        #self.entry.scicat_data.files = []
        #self.entry.scicat_data.sourceFolder = "" # default from sdm
        #self.entry.scicat_data.description = ""
        self.entry.environment_data.title = dct['description']
        self.entry.environment_data.scanID = dct['scannr']

        self.entry.scicat_data.scientificMetadata.update(dct['snapshot'])

        self.posted_detectors = False

    def act_on_data(self, dct):
        """
        Only scan-level information is sent.
        """
        if not self.posted_detectors:
            dets = list(dct.keys())
            # should really remove non-detector things here
            # (search the description? look at the forked Gadget tree?)
            self.entry.environment_data.detectors = sorted(dets)
            self.posted_detectors = True

    def act_on_footer(self, dct):
        """
        Tell SciCat that the scan is done
        """
        if self.verbose:
            print('ScicatRecorder posted this to the database:')
            print(self.entry.show())
        self.entry.end_scan()
