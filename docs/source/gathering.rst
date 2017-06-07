####################
Collecting NMEA Data
####################

Our data gathering application will be a listener. The chartplotter sends a constant
stream of background messages with the requested data injected into that stream.

The collection process looks like this:

1.  Start data gathering.
2.  Fool around on the chartplotter to start transmission of waypoints or routes.
3.  When transmission has ended, stop data gathering.

It's seems difficult to know when the waypoints have all been sent. It may be a 
simple matter of waiting for the background messages to resume. Because the transmission
of waypoints is relatively rare, manually stopping data collection seems simplest.

Data Model
===========

The :class:`nmea_data.Sentence` class defines the essential features of Sentence.

There are a number of subclasses, for a few of the NMEA sentences.

-   :class:`nmeatools.nmea_data.UnknownSentence`
-   :class:`nmeatools.nmea_data.GPRMC`
-   :class:`nmeatools.nmea_data.GPGGA`
-   :class:`nmeatools.nmea_data.GPGLL`
-   :class:`nmeatools.nmea_data.GPGSA`
-   :class:`nmeatools.nmea_data.GPGSV`
-   :class:`nmeatools.nmea_data.GPVTG`
-   :class:`nmeatools.nmea_data.GPZDA`
-   :class:`nmeatools.nmea_data.GPXTE`

The following two are what we're interested in.

-   :class:`nmeatools.nmea_data.GPWPL`. This is the waypoint location. The NMEA sentence
    has three interesting attributes: latitude, longitude, and name.

-   :class:`nmeatools.nmea_data.GPRTE`. This is the container for a route. The NMEA sentence
    is rather complex, because a route can contain a large number of waypoints.
    NMEA messages are kept short, and each sentence will list the names of a few
    waypoints. There's a sequence number that can be used to maintain order
    among the messages.
    
Process
=======

The processing is embodied by :func:`nmeatools.nmea_capture.capture`. This will 
filter the incoming messages, discarding the uninteresting ones and keeping 
all others. These are buffered in memory.

Currently, the background loop messages are hard-wired in the function. 
They can be lifted up into a parameter and an override provided from the command-line.

When ``^c`` is hit, the capture stops, and the captured messages are serialized to a JSON
document.

Example
=======

::

    MacBookPro-SLott:NMEA-Tools slott$ python3 -m nmeatools.nmea_capture /dev/cu.usbserial-A6009TFG
    .........++++++++++..........
    ^CINFO:__main__:Ignored  20
    INFO:__main__:Captured 10
    [...some big JSON...]
    INFO:__main__:Wrote 10 to <stdout>

The ``.`` shows where an ignored message was sent. This is part of the background
loop of sending status information.

The ``+`` shows where a captured waypoint or route message was sent.
