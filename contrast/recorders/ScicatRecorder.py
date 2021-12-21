from . import Recorder
from .Hdf5Recorder import H5_NAME_FORMAT, Link
from .StreamRecorder import walk_dict
from scifish import SciFish
from ..detectors import Detector
from ..utils import str_to_args
import os
import datetime


class ScicatRecorder(Recorder):
    """
    Recorder which submits acquisition info to the SciCat database via a
    helper library.
    """
    def __init__(self, name=None, verbose=False):
        Recorder.__init__(self, name=name)
        self.verbose = verbose

    def act_on_header(self, dct):
        """
        Give SciCat all the info for this scan. Enters the whole snapshot.
        """
        # standard fields
        self.entry = SciFish()
        self.entry.start_scan()
        self.entry.scicat_data.datasetName = dct['scannr']
        self.entry.scicat_data.sampleId = dct['scannr']
        # self.entry.scicat_data.dataFormat = ""
        # self.entry.scicat_data.sourceFolder = "" # default from sdm
        # self.entry.scicat_data.description = ""
        self.entry.environment_data.title = dct['description']
        self.entry.environment_data.scanID = dct['scannr']

        # the scientificMetadata field can be whatever, add the snapshot
        self.entry.scicat_data.scientificMetadata.update(dct['snapshot'])

        # also parse the command and use any keywords, we can use those
        # for general tagging (eg ptycho=True)
        args, kwargs = str_to_args(dct['description'])
        self.entry.scicat_data.scientificMetadata.update(kwargs)

        # First entry of the file list is an ugly guess about what the
        # Hdf5Recorder
        guess = H5_NAME_FORMAT % dct['scannr']
        guess = os.path.join(dct['path'], guess)
        self.file_list = [guess, ]

        # send start, so the entry becomes visible in scanlog
        self.entry.send_start()

        self.posted_detectors = False

    def act_on_data(self, dct):
        """
        Only scan-level information is sent.
        """
        # find a list of detectors
        if not self.posted_detectors:
            dets = list(dct.keys())
            # should really remove non-detector things here
            # (search the description? look at the forked Gadget tree?)
            self.entry.environment_data.detectors = sorted(dets)
            self.posted_detectors = True

        # see if there are some file names passed that should be included
        for d, k, v in walk_dict(dct):
            if isinstance(v, Link):
                if v.filename not in self.file_list:
                    self.file_list.append(v.filename)

    def act_on_footer(self, dct):
        """
        Tell SciCat that the scan is done
        """
        if self.verbose:
            print('ScicatRecorder posted this to the database:')
            print(self.entry.show())

        # deal with the file list (timestamps and sizes)
        files = []
        for fn in self.file_list:
            tm = ''  # UTC iso format, like 2021-11-27T14:29:06.900250
            tm = datetime.utcfromtimestamp(os.path.getmtime()).isoformat()
            sz = os.path.getsize(fn)
            file.append(
                {'path': fn,
                 'time': tm,
                 'size': sz}
            )

        self.entry.end_scan()
