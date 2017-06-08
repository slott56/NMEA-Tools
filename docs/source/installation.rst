#############################
Dependencies and Installation
#############################

Python 3.6. This uses f-strings. It depends on float results in division. It clearly separates text and bytes.

PySerial, version 3.3.

::

    pip install pyserial
    
Download NMEA-Tools.

You *can* install it. It's doubtful, however, that it does exactly what you want.
Since you're going to tinker, it's best to work directly in the repository
that you forked from Git Hub.

::

    export PYTHONPATH=/path/to/NMEA-Tools

Testing
=======

Note that ``nmeatools`` must be visible. When we run ``tests/test.py``, the ``tests``
directory is local and the overall distribution kit directory isn't visible.
By setting :envvar:`PYTHONPATH` we make sure the top-level project directory
(the directory which contains :file:`nmeatools` is visible.

::

    MacBookPro-SLott:NMEA-Tools slott$ PYTHONPATH=. python3 tests/test.py
    ..........
    ----------------------------------------------------------------------
    Ran 10 tests in 0.007s

    OK

Driver
======

I use the driver for by BU-353 GPS antenna. See http://usglobalsat.com/s-122-bu-353-support.aspx
I don't know if this is **required**. If your NMEA-0183 interface device doesn't seem
to work, you may beed an appropriate USB driver.

Using
=====

Once installed, you can mess with

1.  Wiring up the NMEA-0183 to USB connector you've chosen. See :ref:`background`.

2.  Playing with :mod:`nmeatools.nmea_data` which has two simple capture-and-display
    functions: :func:`nmeatools.sample_CP` and :func:`nmeatools.sample_GPS`. 
    
3.  Capturing waypoints and routes using :mod:`nmeatools.nmea_capture`.

4.  Converting NMEA sentences to GPX using :mod:`nmeatools.waypoint_to_gpx`.
