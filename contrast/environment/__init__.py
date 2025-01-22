"""
This module contains the "environment" -- the set of objects that define
how and when data acquisition is done, what is seen, where data is
written, etc. It also provides and keeps track of macros.

The module provides a central instance of the ``Environment`` class,
``env``.
"""

from IPython import get_ipython
from .. import utils
from ..Gadget import Gadget
from .. import colors
from .data import PathFixer
from .scheduling import DummyScheduler
from .snapshots import MotorSnapshot

ipython = get_ipython()


class Env(object):
    """
    Container for a number of global environment variables.
    """
    def __init__(self):
        self.registeredMacros = {}
        self.nextScanID = 0
        self.lastMacroResult = None
        self.userLevel = 5
        self.paths = PathFixer()
        self.scheduler = DummyScheduler()
        self.snapshot = MotorSnapshot()
        self.snapshot.pre_scan = True
        self.snapshot.post_scan = True
        self.check_git_repo()

    def check_git_repo(self):
        self.contrast_git_hash = utils.get_git_revision(short=False)
        self.uncommitted_changes = utils.get_uncommitted_git_changes()

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
      as entered on the command line. They can also be python
      expressions like 1+1 or 1./20, and are converted to strings
      otherwise.
    * Provide a run method which takes no arguments and executes the
      scan or whatever.

    The name of the class converted to lower case will be used for the
    magic command used to launch the macro.
    """

    name = cls.__name__.lower()

    def fcn(line):
        args, kwargs = utils.str_to_args(line)
        try:
            obj = cls(*args, **kwargs)
        except MacroSyntaxError:
            print('Bad input. Usage:')
            print(cls.__doc__)
            return
        obj._command = '%s %s' % (name, line)
        env.lastMacroResult = obj.run()
    if cls.__doc__:
        fcn.__doc__ = cls.__doc__
    else:
        print('Please document your macros! %s is missing a docstring.'
              % cls.__name__)

    # sanity check
    assert cls.run.__call__

    env.registeredMacros[name] = cls
    if not ipython:
        return cls
    ipython.register_magic_function(fcn, magic_name=name)
    return cls


def register_shortcut(name, command):
    """
    Factory function which takes two strings name and command, and creates
    a shortcut macro from the former to the latter.
    """
    def fcn(line):
        runCommand(command)
    fcn.__doc__ = "Shortcut: '%s'" % command
    env.registeredMacros[name] = fcn.__doc__
    ipython.register_magic_function(fcn, magic_name=name)


class MacroSyntaxError(Exception):
    pass


@macro
class LsMac(object):
    """
    List available macros. Do <macro-name>? (without <>) for more information.
    """
    def run(self):
        print(utils.dict_to_table(env.registeredMacros,
                                  titles=('name', 'class'), sort=True))
        print('\nDo <macro-name>? (without <>) for more information.')


@macro
class UserLevel(object):
    """
    Get or set the current user level. ::

        userlevel [<level>]
    """
    def __init__(self, level=None):
        if level is None:
            print("Current userlevel: %d" % env.userLevel)
        else:
            env.userLevel = level

    def run(self):
        pass


@macro
class Path(object):
    """
    Print the current data path.
    """
    def run(self):
        print(f'Current data path:\n\n    {colors.str_path(str(env.paths.directory))}')


@macro
class CheckGit(object):
    """
    checks the git repo of the used contrast installation
    looks the the hash of the used commit
    lists the uncommitted changes
    """
    def run(self):
        env.check_git_repo()

        print(f'git hash of the used contrast installation:')
        print(f'    {env.contrast_git_hash}')

        if env.uncommitted_changes != []:
            print(f'\033[91m[!]\033[0m you are running contrast with uncommitted changes:')
            for fname in env.uncommitted_changes:
                print(f'    {fname}')          

@macro
class HealthCheck(object):
    """
    runs the health check of each gadget in the beamline script
    """
    def __init__(self, *args):
        try:
            self.gadgets_to_check = args
        except (TypeError, IndexError):
            pass
        if not self.gadgets_to_check:
            self.gadgets_to_check = [g for g in Gadget.getinstances()]

    def run(self):
        for g in self.gadgets_to_check:
            if isinstance(g, Gadget):
                g.health_check()
