##########
NMEA-Tools
##########

This is a limited set of Python-based NMEA data acquisition and conversion tools.

The primary user story is this:

    As an owner of several nautical chartplotters, one of which has only NMEA-0183 access,
    I need to extract waypoints and routes from this chartplotter,
    So I can coordinate data between the two devices.
    
Dependencies
============

Python 3.6.  

PySerial 3.3.  https://pypi.python.org/pypi/pyserial

Installation
============

Install pyserial.

Download NMEA-Tools.

You *can* install it. It's doubtful, however, that it does exactly what you want.
Since you're going to tinker, it's best to work directly in the repository
that you forked from Git Hub.

::

    export PYTHONPATH=/path/to/NMEA-tools/nmeatools


More Information
================

See https://slott56.github.io/NMEA-Tools/
