##########
Conversion
##########

There are three sensible targets for conversion.

-   GPX

-   KML

-   CSV


Output Formats
==============

We'll focus on GPX.

GPX
---

See http://www.topografix.com/gpx.asp

We'll bypass formal processing of the XSD definitions.
The data collected is simple. The GPWPL sentence only has lat, lon, ID
The GPRTE sentences only have ID, number/total, and a list of waypoint names.

Template output for the GPX document as a whole:

::

    <gpx
    version="1.1"
    creator="xsd:string [1]"> 
    <metadata> 
        <name> xsd:string </name>
        <desc> xsd:string </desc>
    </metadata>
    <wpt> wptType </wpt>
    <rte> rteType </rte>
    </gpx>

A waypoint (wptType):

::

    <wpt
        lat="latitudeType [1] ?"
        lon="longitudeType [1] ?"> 
        <name> xsd:string </name>
    </wpt>

A route (rteType):

::

    <rte>
        <name> xsd:string </name>
        <number> xsd:nonNegativeInteger </number>
        <desc> xsd:string </desc>
        <rtept> wptType </rtept>
    </rte>
    
KML
---

Here's another XML data structure we could emit.

https://developers.google.com/kml/documentation/kmlreference


CSV
---

There's no formal schema for the CSV representation of points and routes.
In order to work with these, concrete examples from GPSNavX and the new
Zeus2 chart plotter are required.

Conversion Processing
=====================

The conversion process involves two steps.

1.  Load the JSON version of the saved sentences.

2.  Create an XML document using GPX tags.

There are two variations.

-   Convert a saved route.

-   Convert the saved waypoint list.

Each route contains duplicate copies of relevant waypoints. It looks like
GPSNavX handles this by appending a suffix to the waypoint to distinguish 
duplicate copies.

Note that the legacy chartplotter names are highly abbreviated, upper-case only.

After conversion, it's helpful to manually edit the GPX documents to write
more informative waypoint and route names.

Example
=======

::

    MacBookPro-SLott:NMEA-Tools slott$ python3 -m nmeatools.waypoint_to_gpx /Users/slott/Documents/Sailing/Cruise\ History/routes/rt1.json --desc '2017 Waypoints from Red Ranger chartplotter.' --force
    INFO:__main__:Read route from /Users/slott/Documents/Sailing/Cruise History/routes/rt1.json
    INFO:__main__:GPWPL 37°50.45′N 76°16.406′W REEDVILLE
    INFO:__main__:GPWPL 37°50.356′N 76°16.521′W WPT017
    INFO:__main__:GPWPL 37°50.21′N 76°16.701′W WPT018
    INFO:__main__:GPWPL 37°50.081′N 76°16.764′W WPT016
    INFO:__main__:GPWPL 37°49.939′N 76°16.986′W WPT015
    INFO:__main__:GPWPL 37°49.875′N 76°16.911′W COCK CR ST
    INFO:__main__:GPWPL 37°49.35′N 76°16.858′W COCK CR RU
    INFO:__main__:GPWPL 37°49.122′N 76°17.017′W COCK CR 1
    INFO:__main__:GPWPL 37°48.492′N 76°17.557′W GWICO 6
    INFO:__main__:GPWPL 37°48.326′N 76°16.915′W GWICO 4
    INFO:__main__:GPWPL 37°48.007′N 76°15.793′W GWICO 2
    INFO:__main__:GPWPL 37°46.894′N 76°12.375′W GWICO 1
    INFO:__main__:GPWPL 37°40.722′N 76°11.616′W CHES 59A
    INFO:__main__:GPWPL 37°34.341′N 76°11.882′W RAP 2R
    INFO:__main__:GPWPL 37°33.28′N 76°15.51′W PIANK2
    INFO:__main__:GPWPL 37°31.99′N 76°19.02′W PIANK6
    INFO:__main__:GPWPL 37°32.585′N 76°19.172′W JACKSON
    INFO:__main__:GPRTE 'DLTVL RDVL' 1 c ['WPT017', 'WPT018']
    INFO:__main__:GPRTE 'DLTVL RDVL' 2 c ['WPT015', 'COCK CR ST']
    INFO:__main__:GPRTE 'DLTVL RDVL' 3 c ['COCK CR 1', 'GWICO 6']
    INFO:__main__:GPRTE 'DLTVL RDVL' 4 c ['GWICO 2', 'GWICO 1']
    INFO:__main__:GPRTE 'DLTVL RDVL' 5 c ['RAP 2R', 'PIANK2']
    INFO:__main__:GPRTE 'DLTVL RDVL' 6 c ['JACKSON']
    INFO:__main__:23 sentences read
    INFO:__main__:Writing /Users/slott/Documents/Sailing/Cruise History/routes/rt1.gpx

Why are there extra waypoints in the waypoint list that are not referenced in the route?

Your guess is as good as mine.

The names like ``"DLTVL RDVL"`` need to be manually changed in the resulting
GPX file to something like ``"Deltaville to Reedville"``.
