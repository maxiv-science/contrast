from IPython import get_ipython
ipython = get_ipython()

from . import utils
from .data import PathFixer

class Env(object):
    """
    Container for a number of global environment variables.
    """
    def __init__(self):
        self.currentDetectorGroup = None # a DetectorGroup instance
        self.registered_macros = {}
        self.nextScanID = 0
        self.userLevel = 5
        self.paths = PathFixer()
env = Env()

def runCommand(line):
    """
    Function for running magics from scripts.
    """
    ipython.magic(line)

def macro(cls):
    """
    Decorator which turn a class into a macro. This means that it will
    be callable from the ipython prompt with command line syntax.

    * Take all arguments in the constructor. The arguments can be Gadget
      objects and this decorator will find the objects from their names
      as entered on the command line.
    * Provide a run method which takes no arguments and executes the 
      scan or whatever.

    The name of the class converted to lower case will be used for the
    magic command used to launch the macro.
    """
    if not ipython: return cls

    def fcn(line):
        args = utils.str_to_args(line)
        obj = cls(*args)
        obj.run()
    if cls.__doc__:
        fcn.__doc__ = cls.__doc__
    else:
        print('Please document your macros! %s is missing a docstring.'\
                % cls.__name__)

    # sanity check
    assert cls.run.__call__

    name = cls.__name__.lower()
    env.registered_macros[name] = cls
    ipython.register_magic_function(fcn, magic_name=name)
    return cls

@macro
class LsMac(object):
    """
    List available macros. Do <macro-name>? (without <>) for more information.
    """
    def run(self):
        print(utils.dict_to_table(env.registered_macros, titles=('name', 'class')))
