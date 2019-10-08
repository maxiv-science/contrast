from .Motor import Motor, DummyMotor, MotorMemorizer
from .PseudoMotor import PseudoMotor, ExamplePseudoMotor

def all_are_motors(seq):
    """
    Function which returns True if all objects in seq are instances
    of Motor or its subclasses.
    """
    checks = [isinstance(m, Motor) for m in seq]
    return not (False in checks)

# don't automatically import hardware-specific classes here,
# as these might have special dependencies that aren't
# available everywhere.
