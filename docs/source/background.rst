..  _background:

##########
Background
##########

The migration of data from an old chartplotter to other plotters decomposes into two other problems.

1.  Get data from the chartplotter which only supports an NMEA-0183 interface.
    The device can "send" waypoints and routes over the interface wire, 
    but there's no common device or network interface.
    
2.  Convert the data to a format usable by the others. The NMEA-0183
    sentences are not widely used. GPX format is more widely used.
    
Once the data has been converted from NMEA sentences to a GPX file, it can
be placed onto a Micro-SD card for transfer to the new chartplotter [#]_ that has a modern
set of interfaces.

.. [#] B&G Zeus 2. https://bandg.com/product/zeus2_9/ 

Along the way, it can be used to populate waypoints and routes in `GPSNavX <http://gpsnavx.com>`_, 
running on a Mac laptop. This is how the files are captured in the first place, and it's how 
the Micro-SD card is written to move files to the new chartplotter.

With some effort, the files can be transfered via http://X-Traverse.com (the Fugawi shop) to 
`iNavX <http://inavx.com/?ref=gpsnavx.com>`_ running on an iPad. 

The reverse direction is also interesting, but not needed -- yet.

About NMEA
===============

NMEA-0183 is used by numerous marine devices. It's defined to use EIA-422 wiring.
It's called "point-to-point, multidropped". A single driver can have multiple receivers.

In most simple marine applications, a chart plotter and radio or chart plotter, radio, and
radar might be interconnected. In these applications, the chartplotter would be a hub
with several available channels.

NMEA "talkers" provide data in Sentences. Each sentence begins with ``'$'``. A ``'*'`` signals
the end; this is followed by a checksum byte as two ASCII characters.

NMEA "listeners" gather the data. 

Generally, a talker will provide a sequence of messages followed by a short delay. 
In the chart-plotter case, there might be an eight message loop providing information
like the following: 

-   Cross-track error and steering,
-   Recommended Minimum "C" (position, velocity, time),
-   Depth Below Transducer,
-   Depth,
-   Temperature of water,
-   Velocity and Heading of water,
-   GPS Fix,
-   GPS Lat-Lon.

There's considerable redundancy in this. The idea, however, is to have each
device listen for only the relevant message, ignoring all others.

When we send waypoints (or routes) from device to device, the waypoint data is inserted
into the stream of messages to all listeners. Once the waypoints (or routes) have been 
sent, the background loop of data resumes. There's no formal bracket for the data.

See also:

-   https://www.sparkfun.com/datasheets/GPS/NMEA%20Reference%20Manual-Rev2.1-Dec07.pdf

-   https://en.wikipedia.org/wiki/NMEA_0183

-   http://www.gpsinformation.org/dale/nmea.htm

NMEA Hardware interface
=======================

http://www.digitalyachtamerica.com/index.php/en/products/interfacing/nmeausb/product/67-usb-to-nmea-adaptor

How is this wired?

http://www.standardhorizon.co.uk/files/CP180&CP300_16.60%20O_e121211.pdf

The target chartplotter is a Standard Horizon CP300i. There are five ports 
available. The following wiring is for port #1. 

..  csv-table::

    CP300i,USB Adaptor
    Green,Black
    Blue,Orange
    Brown,Yellow
    
The hardward will operate at:

-   Baud Rate: 4800
-   Parity: None
-   Data Bits: 8
-   Stop Bits: 1
-   Flow Control: None

Most of these are default settings for pyserial.

NMEA Sentence Protocol
======================

NMEA sentences are sent as a stream of ASCII bytes. Sentences begin with ``'$'`` (or ``'!'``)
and end with ``'*xx'`` where ``xx`` are the two hex digits of the message checksum byte.

Here's an example message::

    b"$GPGSA,A,2,29,19,28,,,,,,,,,,23.4,12.1,20.0*0F"
    
The hex ``0F`` at the end is the xor-reduction of the bytes in the message prior 
to the ``*``. 
    
The data gathering algorithm is an iterator that produces valid sentences.

::

    from nmea_data import Scanner
    with Scanner(device) as GPS:
        for sentence_fields in GPS:
            print(sentence_fields)
            
The output will be a sequence of NMEA sentences, each sentence decomposed into
strings of bytes broken on the ``","`` boundaries. The ``"$"`` and ``"*xx"`` have been removed,
leaving the talker type (``"GP"``) and sentence type (``"GSA"``) with the various fields.

Given a sequence of byte values, we can then create a specific subclass of Sentence
that decodes the values inside the message.

For example::

    $GPGLL,2542.9243,N,08013.6310,W,162823.000,A*29
    
Can be unpacked as this::

    [b'GPGLL', b'2542.9243', b'N', b'08013.6310', b'W', b'162823.000', b'A']

The map from positional values works like this:

..  csv-table::

    position,description,attribute,conversion function
    1,'Latitude', 'lat', lat
    2,'N/S Indicator', 'lat_h', text
    3,'Longitude', 'lon', lon
    4,'E/W Indicator', 'lon_h', text
    5,'UTC Time', 'time_utc', utc_time
    6,'Status', 'status', text

This requires a number of conversion functions, including ``lat()``, ``lon()``, ``text()``, 
and ``utc_time()`` to unpack the bytes into useful values.

For example: ``2542.9243`` is ``25°42.9243′``. This can be turned into ``25.715405``, also.

Conversions
===========

We can identify a number of types of conversion functions.

-   :func:`nmeatools.nmea_data.text`

-   :func:`nmeatools.nmea_data.utc_time`

-   :func:`nmeatools.nmea_data.utc_date`

-   :func:`nmeatools.nmea_data.lat`

-   :func:`nmeatools.nmea_data.lon`

-   :func:`nmeatools.nmea_data.nfloat`

-   :func:`nmeatools.nmea_data.nint`

This covers the bases for the values seen in the messages of interest.

Serialization
=============

We can, of course, serialize sentences in bytes. 

However, these are painful to work with.

To slightly simplify life, it's easier to define a JSON encoder and JSON decoder.

-   :class:`nmeatools.nmea_data.Encoder`

-   :class:`nmeatools.nmea_data.Decoder`

These can serialize and deserialize sentences.
