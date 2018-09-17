from Gadget import Gadget
import Recorder
import utils
from IPython import get_ipython
ipython = get_ipython()

print(__name__)

### We will use a number of global "environment" variables.
currentDetectorGroup = None # a DetectorGroup instance
registered_macros = {}
nextScanID = 0
userLevel = 5

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

    # sanity check
    assert cls.run.__call__

    name = cls.__name__.lower()
    registered_macros[name] = cls
    ipython.register_magic_function(fcn, magic_name=name)
    return cls

@macro
class LsMac(object):
    def run(self):
        print(utils.dict_to_table(registered_macros, titles=('name', 'class')))


### the following should go in Recorders, but can't get that to work.

def active_recorders():
    return [r for r in Recorder.Recorder.getinstances() if r.is_alive()]

@macro
class LsRec(object):
    def run(self):
        dct = {r.name: r.__class__ for r in active_recorders()}
        print(utils.dict_to_table(dct, titles=('name', 'class')))

@macro
class LivePlot(object):
   def __init__(self, xdata, ydata, name='plot'):
       self.xdata = xdata.name
       self.ydata = ydata.name
       self.name = name
   def run(self):
       rec = Recorder.PlotRecorder(self.xdata, self.ydata, self.name)
       rec.start()
