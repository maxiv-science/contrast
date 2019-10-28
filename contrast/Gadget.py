import weakref

class Gadget(object):
    """
    Base class for motors, detectors, etc. Main purpose is to keep track
    of instances so that names can be mapped to objects.

    This base class keeps a master class attribute holding references to
    all instances. The class method getinstances() on each subclass then
    filters and returns instances of that class or its children.

    """

    _base_class_instances = set()

    def __init__(self, name=None, userlevel=1):
        if not str(name) == name:
            raise Exception('Gadgets must have names!')
        self.name = name
        self.userlevel = userlevel
        self._base_class_instances.add(weakref.ref(self))

    @classmethod
    def getinstances(cls):
        """
        Returns a generator over all instances of this class and its children. ::

            [g.name for g in Gadget.getinstances()]      # a list of all motors, detectors, etc.
            [m.name for m in Motor.getinstances()]       # a list of all motors.
            [m.name for m in DummyMotor.getinstances()]  # a list of all dummy motors.
        """
        dead = set()
        for ref in cls._base_class_instances:
            obj = ref()
            if isinstance(obj, cls):
                yield obj
            elif obj is None:
                dead.add(ref)
        cls._base_class_instances -= dead
