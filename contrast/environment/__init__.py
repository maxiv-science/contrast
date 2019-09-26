"""
This module contains the "environment" -- the set of objects that define how
and when data acquisition is done, what is seen, where data is written, etc.
It also provides and keeps track of macros.

The module provides a central instance of the Environment class, env.
"""

from IPython import get_ipython
ipython = get_ipython()

from .. import utils
from .data import PathFixer
from .scheduling import DummyScheduler
from .snapshots import MotorSnapshot

class Env(object):
    """
    Container for a number of global environment variables.
    """
    def __init__(self):
        self.registeredMacros = {}
        self.nextScanID = 0
        self.userLevel = 5
        self.paths = PathFixer()
        self.scheduler = DummyScheduler()
        self.snapshot = MotorSnapshot()
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
      as entered on the command line. They can also be python expressions
      like 1+1 or 1./20.
    * Provide a run method which takes no arguments and executes the 
      scan or whatever.

    The name of the class converted to lower case will be used for the
    magic command used to launch the macro.
    """
    if not ipython: return cls

    def fcn(line):
        args = utils.str_to_args(line)
        try:
            obj = cls(*args)
        except MacroSyntaxError:
            print('Bad input. Usage:')
            print(cls.__doc__)
            return
        obj.run()
    if cls.__doc__:
        fcn.__doc__ = cls.__doc__
    else:
        print('Please document your macros! %s is missing a docstring.'\
                % cls.__name__)

    # sanity check
    assert cls.run.__call__

    name = cls.__name__.lower()
    env.registeredMacros[name] = cls
    ipython.register_magic_function(fcn, magic_name=name)
    return cls

class MacroSyntaxError(Exception):
    pass

@macro
class LsMac(object):
    """
    List available macros. Do <macro-name>? (without <>) for more information.
    """
    def run(self):
        print(utils.dict_to_table(env.registeredMacros, titles=('name', 'class'), sort=True))
        print('\nDo <macro-name>? (without <>) for more information.')

@macro
class UserLevel(object):
    """
    Get or set the current user level

    userlevel [<level>]
    """
    def __init__(self, level=None):
        if level is None:
            print("Current userlevel: %d" % env.userLevel)
        else:
            env.userLevel = level
    def run(self):
        pass


