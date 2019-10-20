Concepts
========

Contrast is a beamline interface based on IPython. The code is organized as a library containing various classes. A beamline is set up simply by making instances for detectors, motors, and any other devices directly in IPython or in a script.

Contrast conceptually does three things,

1. Represents and keeps track of beamline components as python objects.
2. Provides shorthand macros to do orchestrated operations on these devices.
3. Keeps track of the environment in which the instrument is run.

``Gadget`` and its subclasses
-----------------------------

Contrast classes which represent specific beamline components (hardware or software) inherit from the common ``Gadget`` base class. Its most important subclasses are ``Motor`` (primarily for affecting some aspect of reality), ``Detector`` (for measuring some facet of the universe) and ``Recorder`` (for saving or passing on data).

.. inheritance-diagram:: contrast.motors.Motor.Motor contrast.detectors.Detector.TriggerSource contrast.recorders.Recorder.Recorder
    :parts: 1
    :top-classes: contrast.recorders.Recorder.Process

Instead of keeping central registries or databases, Contrast keeps track of ``Gadget`` objects through instance tracking and inheritance. The base class or any of its children can report what instances exist, and calling the ``getinstances()`` method of classes at different levels serves to filter out the objects of interest. An example follows. ::

    In [1]: [m.name for m in Motor.getinstances()]
    Out[1]: ['gap', 'samy', 'samx']

    In [2]: [d.name for d in Detector.getinstances()]
    Out[2]: ['det1', 'det3', 'det2']

    In [3]: [g.name for g in Gadget.getinstances()]
    Out[3]: ['gap', 'detgrp', 'det1', 'samy', 'samx', 'det3', 'det2', 'hdf5recorder']

Motors
~~~~~~

Detectors
~~~~~~~~~

Recorders
~~~~~~~~~

Data is captured by recorders. Recorders are run in separate processes and get data through queues, avoiding holding up the main acquisition loop because of I/O. They can do anything with the data, for example saving to ``hdf5`` files, live plotting, or streaming. See the ``Hdf5Recorder``, ``PlotRecorder``, and ``StreamRecorder`` classes for examples.

Note how easy it is to write these recorders, and how easy it would be to integrate online data analysis.

The ``lsrec`` macro lists currently running recorders. ::

    In [30]: lsrec

    name           class                                            
    ----------------------------------------------------------------
    hdf5recorder   <class 'lib.recorders.Hdf5Recorder.Hdf5Recorder'>
    name           <class 'lib.recorders.PlotRecorder.PlotRecorder'>


Macros
------

A macro is a short expression in command line syntax which can be directly run at the ipython prompt. The following is a macro. ::

    mv samx 12.4

In this framework, macros are created by writing a class with certain properties and marking that class with a decorator. This registers the macro as a magic ipython command. All available macros are stored in a central list, and can be listed with the ``lsmac`` command. The macro syntax is similar to sardana and spec. ::

    In [1]: import contrast

    In [3]: %lsmac

    name         class                                             
    ---------------------------------------------------------------
    activate     <class 'contrast.detectors.Detector.Activate'>    
    ascan        <class 'contrast.scans.AScan.AScan'>              
    ct           <class 'contrast.scans.Scan.Ct'>                  
    deactivate   <class 'contrast.detectors.Detector.Deactivate'>  
    dmesh        <class 'contrast.scans.Mesh.DMesh'>               
    dscan        <class 'contrast.scans.AScan.DScan'>              
    liveplot     <class 'contrast.recorders.PlotRecorder.LivePlot'>
    loopscan     <class 'contrast.scans.Scan.LoopScan'>            
    lsdet        <class 'contrast.detectors.Detector.LsDet'>       
    lsm          <class 'contrast.motors.Motor.LsM'>               
    lsmac        <class 'contrast.environment.LsMac'>              
    lsrec        <class 'contrast.recorders.Recorder.LsRec'>       
    lstrig       <class 'contrast.detectors.Detector.LsTrig'>      
    mesh         <class 'contrast.scans.Mesh.Mesh'>                
    mv           <class 'contrast.motors.Motor.Mv'>                
    mvd          <class 'contrast.motors.Motor.Mvd'>               
    mvr          <class 'contrast.motors.Motor.Mvr'>               
    path         <class 'contrast.environment.Path'>               
    setlim       <class 'contrast.motors.Motor.SetLim'>            
    setpos       <class 'contrast.motors.Motor.SetPos'>            
    spiralscan   <class 'contrast.scans.Spiral.SpiralScan'>        
    startlive    <class 'contrast.detectors.Detector.StartLive'>   
    stoplive     <class 'contrast.detectors.Detector.StopLive'>    
    tweak        <class 'contrast.scans.Tweak.Tweak'>              
    umv          <class 'contrast.motors.Motor.Umv'>               
    umvr         <class 'contrast.motors.Motor.Umvr'>              
    userlevel    <class 'contrast.environment.UserLevel'>          
    wa           <class 'contrast.motors.Motor.Wa'>                
    wm           <class 'contrast.motors.Motor.Wm'>                
    wms          <class 'contrast.motors.Motor.WmS'>               

    Do <macro-name>? (without <>) for more information.

Note how macros aren't stored in a special library. They are written throughout the library wherever they make sense. For example, in ``Detector.py`` where the detector base classes are defined, the ``lsdet`` macro is defined as follows.

::

    @macro
    class LsDet(object):
        def run(self):
            dct = {d.name: d.__class__ for d in Detector.getinstances()}
            print(utils.dict_to_table(dct, titles=('name', 'class')))

Also note that a macro is different from a script. Anyone can easily write a macro, but for composite operations where existing macros are just combined it is faster to write a script. The following is a script, not a macro, but uses a special ``runCommand`` function to interface with the command line syntax. ::

    from lib.environment import runCommand

    for i in range(5):
        runCommand('mv samy %d' % new_y_pos)
        runCommand('ascan samx 0 1 5 .1')

The environment object
----------------------

No global environment variables are used. Instead, a central object in the environment module is used to store values such as scan number etc. ::

    In [24]: from lib.environment import env

    In [25]: env.nextScanID
    Out[25]: 1

In fact, the central object ``env`` manages the overall logistics of the beamline. For example, where to save data, what macros are registered, whether there are events like storage ring topups to keep track of, how to capture the state of the istrument before gathering data, etc. For each of these tasks, ``env`` keeps references to such manager objects that handle the specifics of the configured instrument.
