# contrast
Light weight data acquisition framework for orchestrating beamline experiments.

The code is organized as a library containing various classes. A beamline is set up simply by making instances for detectors, motors, and any other devices directly in ipython. See `dummy_beamline.py` for example.

## macros
A macro is a short expression in command line syntax which can be directly run at the ipython prompt. The following is a macro.
```
mv samx 12.4
```

In this framework, macros are created by writing a class with certain properties and marking that class with a decorator. This registers the macro as a magic ipython command. All available macros are stored in a central list, and can be listed with the `lsmac` command. The macro syntax is similar to sardana and spec.
```
In [2]: lsmac

name            class                                          
---------------------------------------------------------------
ascan           <class 'lib.scans.AScan.AScan'>                
ct              <class 'lib.scans.Scan.Ct'>                    
dmesh           <class 'lib.scans.Mesh.DMesh'>                 
dscan           <class 'lib.scans.AScan.DScan'>                
liveplot        <class 'lib.recorders.PlotRecorder.LivePlot'>  
loopscan        <class 'lib.scans.Scan.LoopScan'>              
lsdet           <class 'lib.detectors.Detector.LsDet'>         
lsm             <class 'lib.motors.Motor.LsM'>                 
lsmac           <class 'lib.environment.LsMac'>                
lsrec           <class 'lib.recorders.Recorder.LsRec'>         
mesh            <class 'lib.scans.Mesh.Mesh'>                  
mv              <class 'lib.motors.Motor.Mv'>                  
mvd             <class 'lib.motors.Motor.Mvd'>                 
mvr             <class 'lib.motors.Motor.Mvr'>                 
npointflyscan   <class 'lib.scans.NpointFlyscan.NpointFlyscan'>
setlim          <class 'lib.motors.Motor.SetLim'>              
setpos          <class 'lib.motors.Motor.SetPos'>              
spiralscan      <class 'lib.scans.Spiral.SpiralScan'>          
startlive       <class 'lib.detectors.Detector.StartLive'>     
stoplive        <class 'lib.detectors.Detector.StopLive'>      
tweak           <class 'lib.scans.Tweak.Tweak'>                
userlevel       <class 'lib.environment.UserLevel'>            
wa              <class 'lib.motors.Motor.Wa'>                  
wm              <class 'lib.motors.Motor.Wm'>                  

Do <macro-name>? (without <>) for more information.
```

Note how macros aren't stored in a special library. They are written throughout the library wherever they make sense. For example, in `Detector.py` where the detector base classes are defined, the `lsdet` macro is defined as follows.
```
@macro
class LsDet(object):
    def run(self):
        dct = {d.name: d.__class__ for d in Detector.getinstances()}
        print(utils.dict_to_table(dct, titles=('name', 'class')))
```

Note that a macro is different from a script. Anyone can easily write a macro, but for composite operations where existing macros are just combined it is faster to write a script. The following is a script, not a macro, but uses a special `runCommand` function to interface with the command line syntax.
```
from lib.environment import runCommand

for i in range(5):
    runCommand('mv samy %d' % new_y_pos)
    runCommand('ascan samx 0 1 5 .1')

```

## environment variables
No global environment variables are used. Instead, a central object in the environment module is used to store values such as scan number etc.
```
In [24]: from lib.environment import env

In [25]: env.nextScanID
Out[25]: 1
```

## detector selection
Detectors have an `active` attribute which determines if they are included in data acquisition such as scans. The macro `lsdet` indicates if each detector is active with an asterisk.
```
In [2]: lsdet

  name   class                                          
--------------------------------------------------------
* det2   <class 'lib.detectors.Dummies.DummyDetector'>  
* det3   <class 'lib.detectors.Dummies.Dummy1dDetector'>
* det1   <class 'lib.detectors.Dummies.DummyDetector'>  

In [3]: ct
det2 : 0.5862324427414796
det3 : (100,)
det1 : 0.815299279368746

In [4]: det3.active=False

In [5]: lsdet

  name   class                                          
--------------------------------------------------------
* det2   <class 'lib.detectors.Dummies.DummyDetector'>  
  det3   <class 'lib.detectors.Dummies.Dummy1dDetector'>
* det1   <class 'lib.detectors.Dummies.DummyDetector'>  

In [6]: ct
det2 : 0.26999817158517125
det1 : 0.4045182722290984
```

## instance tracking
The framework has no databases or central registries. Instead, objects are related through inheritance. A common base class `Gadget`
is inherited by detectors, motors, as all the rest. `Gadget` and all of its subclasses keep track of their instances. An example follows.
```
In [1]: [m.name for m in Motor.getinstances()]
Out[1]: ['gap', 'samy', 'samx']

In [2]: [d.name for d in Detector.getinstances()]
Out[2]: ['det1', 'det3', 'det2']

In [3]: [g.name for g in Gadget.getinstances()]
Out[3]: ['gap', 'detgrp', 'det1', 'samy', 'samx', 'det3', 'det2', 'hdf5recorder']
```
 
## recorders
Data is captured by recorders. Recorders are run in separate processes and get data through queues, avoiding holding up the main acquisition loop because of I/O. They can do anything with the data, for example saving to `hdf5` files or live plotting. See the `Hdf5Recorder` and `PlotRecorder` classes for examples. The former is very primitive still, but the latter is quite nice.

Note how easy it is to write these recorders, and how easy it would be to integrate online data analysis, for example writing a recorder which serves data (or links to data) for an on-the-fly ptycho engine to grab.

The `lsrec` macro lists currently running recorders.
```
In [30]: lsrec

name           class                                            
----------------------------------------------------------------
hdf5recorder   <class 'lib.recorders.Hdf5Recorder.Hdf5Recorder'>
name           <class 'lib.recorders.PlotRecorder.PlotRecorder'>
```

## user levels
All `Gadget` instances have an associated user level. This means that certain motors can be hidden and protected while others are exposed through the macros. In this example, two sample motors are available to everyone while the undulator gap is higher level. This is not a security feature but meant to simplify the environment and reduce the risk of mistakes
```
In [7]: env.userLevel
Out[7]: 1

In [8]: wa
samy 0.0
samx 0.0

In [9]: env.userLevel = 5

In [10]: wa
samy 0.0
gap 0.0
samx 0.0
```

## direct access to python objects
If `Gadget` objects operate on underlying Tango devices, then Tango attributes are directly accessible on the objects themselvs. PyTango provides tab completion and so these can be easily checked or corrected. Of course `Gadget`subclasses can provide nice getter and setter methods, but fixes are easily done.
```
In [7]: pilatus.det.energy
Out[7]: 10.0

In[8]: pilatus.lima.saving_mode
Out[8]: 'MANUAL'
```

