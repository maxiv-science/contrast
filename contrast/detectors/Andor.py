from .Lima import LimaDetector

class Andor(LimaDetector):
    def __init__(self, *args, **kwargs):
        super(Andor, self).__init__(*args, **kwargs)
        self._hdf_path_base = 'entry_%04d/measurement/Andor/data/array'

    def _initialize_det(self):
        self.lima.user_detector_name = 'Andor'

