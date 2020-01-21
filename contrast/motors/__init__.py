"""
Provides the ``Motor`` base class and derived motor classes.

Does not automatically load hardware-specific submodules or classes
as these might have special dependencies that aren't available
everywhere.
"""

from .Motor import Motor, DummyMotor, MotorMemorizer, MotorBookmark
from .PseudoMotor import PseudoMotor, ExamplePseudoMotor

def all_are_motors(seq):
    """
    Function which returns True if all objects in seq are instances
    of Motor or its subclasses.

    :param seq: List or tuple of objects to check
    """
    checks = [isinstance(m, Motor) for m in seq]
    return not (False in checks)
