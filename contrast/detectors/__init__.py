"""
Provides the ``Detector`` base class, base classes that bring other
functionality, as well as derived detector subclasses.

Does not automatically load hardware-specific submodules or classes
as these might have special dependencies that aren't available
everywhere.
"""


from .Detector import Detector, TriggerSource, DetectorGroup, LiveDetector, TriggeredDetector
from .Dummies import DummyDetector, Dummy1dDetector, DummyWritingDetector, DummyWritingDetector2, DummyDictDetector, DummyTriggerSource
from .Pseudo import PseudoDetector
