import weakref

print(__name__)

class Gadget(object):
    """
    Base class for motors, detectors, etc. Main purpose is to keep track
    of instances so that names can be mapped to objects.

    This base class keeps a master class attribute holding references to
    all instances. The class method getinstances() on each subclass then
    filters and returns instances of that class or its children.

    So:
    [g.name for g in Gadget.getinstances()]         # is a list of all motors, detectors, and all else.
    [m.name for m in Motor.getinstances()]          # is a list of all motors.
    [m.name for m in DummyMotor.getinstances()]     # is a list of all dummy motors.

    """

    _base_class_instances = set()

    def __init__(self, name=None):
        if not str(name) == name:
            raise Exception('Gadgets must have names!')
        self.name = name
        self._base_class_instances.add(weakref.ref(self))

    @classmethod
    def getinstances(cls):
        """
        Smart method stolen from effbot.org and modified.
        """
        dead = set()
        for ref in cls._base_class_instances:
            obj = ref()
            if isinstance(obj, cls):
                yield obj
            elif obj is None:
                dead.add(ref)
        cls._base_class_instances -= dead