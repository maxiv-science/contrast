Built-in macros
===============

activate
--------

    Activates all detectors or those specified. ::

        activate [<det1> ... <detN>]
    

ascan
-----

    Software scan one or more motors in parallel. ::
        
        ascan <motor1> <start> <stop> ... <intervals> <exp_time>
    

ct
--

    Make a single acquisition on the active detectors without recording
    data. Optional argument <exp_time> specifies exposure time, the default
    is 1.0. ::

        ct [<exp_time>]
    

deactivate
----------

    Deactivates all detectors or those specified. ::

        deactivate [<det1> ... <detN>]
    

dmesh
-----

    Software scan on a regular grid of N motors, with positions relative
    to each motor's current one. Moves motors back at the end. ::

        dmesh <motor1> <start> <stop> <intervals> ... <exp_time>
    

dscan
-----

    Software scan one or more motors in parallel, with positions
    relative to each motor's current one. Moves back afterwards. ::

        dscan <motor1> <start> <stop> <intervals> ... <exp_time>
    

liveplot
--------

    Start a live plot recorder which will plot coming scans. ::

        liveplot [<x>] <y>

    Examples::

        liveplot xmotor diode1
        liveplot diode1
    

loopscan
--------

    A software scan with no motor movements. Number of exposures is
    <intervals> + 1, for consistency with ascan, dscan etc. ::

        loopscan <intervals> <exp_time>
    

lsdet
-----

    List available detectors.
    

lsm
---

    List available motors.
    

lsmac
-----

    List available macros. Do <macro-name>? (without <>) for more information.
    

lsrec
-----

    List active recorders.
    

lstrig
------

    List available trigger sources.
    

mesh
----

    Software scan on a regular grid of N motors. ::
        
        mesh <motor1> <start> <stop> <intervals> ... <exp_time>
    

mv
--

    Move one or more motors. ::

        mvr <motor1> <position1> <motor2> <position2> ...

    

mvd
---

    Move one or more motors to an abolute dial position. Not implemented.
    

mvr
---

    Move one or more motors relative to their current positions. ::

        mvr <motor1> <position1> <motor2> <position2> ...

    

path
----

    Print the current data path.
    

setlim
------

    Set limits on motors. ::

        setlim <motor1> <lower 1> <upper 1> ...
    

setpos
------

    Sets user position on motors. ::

        setpos <motor1> <pos1> ...
    

spiralscan
----------

    Software scan across a 2D Archimedes spiral centered on the 
    current position. ::
        
        spiralscan <motor1> <motor2> <stepsize> <positions> <exp_time>
    

startlive
---------

    Starts software live mode on listed eligible detectors. If none
    are listed, all active and eligible detectors are started. ::

        startlive [<det1> ... <detN> <exposure time>]
    

stoplive
--------

    Stops software live mode on listed eligible detectors. If
    no arguments are given, all active live detectors are
    stopped. ::

        stoplive [<det1> ... <detN>]
    

tweak
-----

    An interactive scan where motor positions are chosen manually for
    each point. Useful for tweaking motors and reading the currently
    active detectors after each step. ::

        tweak <motor1> <stepsize1> [<motor2> <stepsize2>] <exp_time>
    

umv
---

    Like mv, but prints the current position while moving, and returns
    when the move is complete.
    

umvr
----

    Like umv, but in positions relative to the current ones.
    

userlevel
---------

    Get or set the current user level. ::

        userlevel [<level>]
    

wa
--

    Print the positions of all motors available at the current user level.
    

wm
--

    Print the positions of one or more motors. ::

        wm <motor1> <motor2> ...
    

wms
---

    Silent 'where motor'. Print the positions of one or more motors but do not print any output. ::

        wms <motor1> <motor2> ...
    

