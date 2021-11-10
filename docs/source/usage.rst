Installation and usage
======================

Launching a beamline
--------------------
::

    ipython3
    %run /path/to/your/beamline/script.py

or

::

    ipython3 -i /path/to/your/beamline/script.py

Detector selection
------------------

Detectors have an ``active`` attribute which determines if they are included in data acquisition such as scans. The macro ``%lsdet`` indicates if each detector is active with an asterisk. ::

    In [2]: lsdet

      name   class                                          
    -------------------------------------------------------------
    * det2   <class 'contrast.detectors.Dummies.DummyDetector'>  
    * det3   <class 'contrast.detectors.Dummies.Dummy1dDetector'>
    * det1   <class 'contrast.detectors.Dummies.DummyDetector'>  

    In [3]: ct
    det2 : 0.5862324427414796
    det3 : (100,)
    det1 : 0.815299279368746

    In [4]: det3.active=False

    In [5]: lsdet

      name   class                                          
    -------------------------------------------------------------
    * det2   <class 'contrast.detectors.Dummies.DummyDetector'>  
      det3   <class 'contrast.detectors.Dummies.Dummy1dDetector'>
    * det1   <class 'contrast.detectors.Dummies.DummyDetector'>  

    In [6]: ct
    det2 : 0.26999817158517125
    det1 : 0.4045182722290984

User levels
-----------

All :py:class:`~contrast.Gadget.Gadget` instances have an associated user level. This means that certain motors can be hidden and protected while others are exposed through the macros. In this example, two sample motors are available to everyone while the undulator gap is higher level. This is not a security feature but meant to simplify the environment and reduce the risk of mistakes. ::

    In [4]: %userlevel
    Current userlevel: 1

    In [5]: wa
    motor     user pos.  limits            dial pos.  limits       
    ---------------------------------------------------------------
    samx      0.00       (0.00, 10.00)     0.00       (0.00, 10.00)
    samy      0.00       (-5.00, 5.00)     0.00       (-5.00, 5.00)

    In [6]: %userlevel 5

    In [7]: wa
    motor     user pos.  limits            dial pos.  limits       
    ---------------------------------------------------------------
    gap       0.00000    (None, None)      0.00       (None, None) 
    samx      0.00       (0.00, 10.00)     0.00       (0.00, 10.00)
    samy      0.00       (-5.00, 5.00)     0.00       (-5.00, 5.00)

Defining custom macros
----------------------

To write your own macro, simply write a class exposing an ``__init__`` and a ``run`` method, and decorate it with ``@macro`` as above. The ``__init__`` method gets the macro command-line arguments as positional arguments, while ``run`` should take no arguments. So, for example, the macro defined as::

    In [12]: from contrast.environment import macro

    In [13]: @macro
        ...: class My_Macro(object):
        ...:     """ My test macro """
        ...:     def __init__(self, arg1, arg2):
        ...:         self.arg1 = arg1
        ...:         self.arg2 = arg2
        ...:     def run(self):
        ...:         print(self.arg1, self.arg2)
        ...:         

can be run like this. ::

    In [14]: %my_macro 1 2
    1 2

Place your macro in your favourite folder, and make sure to use absolute imports (``from contrast...``). Load the macro by running the file in your
ipython interpreter. ::

    %run /path/to/macro/file.py

Getting information out of macros
---------------------------------

Although direct access to python objects allows you to probe the state of Gadgets, ::

    In [7]: gap.user_position
    Out[7]: 3.14

it is sometimes convenient to get results from macros. The ``run()`` method on macros can return usefult information. This can be done by manually constructing and running the macro object, ::

    In [9]: from contrast.motors.Motor import Wm
    In [10]: obj = Wm(gap)
    In [11]: g = obj.run()
    In [12]: g
    Out[12]: 3.14

but in case you just want to execute a command without having to look up the python object at all, the output from the latest executed macro can always be found attached to the central ``env`` object. ::

    In [13]: wm gap
    motor     user pos.  limits           dial pos.  limits      
    -------------------------------------------------------------
    gap       3.14000    (None, None)     3.14       (None, None)

    In [14]: env.lastMacroResult
    Out[14]: 3.14

If you're not on the ipython console but in a script, this still works. ::

    In [15]: from contrast.environment import runCommand
    In [16]: runCommand('wm gap')
    motor     user pos.  limits           dial pos.  limits
    -------------------------------------------------------------
    gap       3.14000    (None, None)     3.14       (None, None)

    In [17]: env.lastMacroResult
    Out[17]: 3.14

Direct access to python objects
-------------------------------

If :py:class:`~contrast.Gadget.Gadget` objects operate on underlying Tango devices, then Tango attributes are directly accessible on the objects themselves. PyTango provides tab completion and so these can be easily checked or corrected. Of course :py:class:`~contrast.Gadget.Gadget` subclasses can provide nice getter and setter methods, but fixes are easily done. ::

    In [7]: pilatus.det.energy
    Out[7]: 10.0

    In[8]: pilatus.lima.saving_mode
    Out[8]: 'MANUAL'
