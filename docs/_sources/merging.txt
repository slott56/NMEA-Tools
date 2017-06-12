########
Merging
########

A rather complex operation involves merging new waypoints 
into an existing chartplotters set of waypoints.

The reason it's interesting is the need to remove duplicates.

Simple duplication by name is a potential problem. However, 
names are not really **required** to be globally unique. 
Because routes include copies of selected waypoints -- chosen by location --
there's no reason for a name to be globally unique.

The duplicates must be flagged by location. Two names for the
same waypoint are more of a problem than two waypoints named "Fish Trap".

Data Model
==========

There are two inputs:

-   An extract from the new chartplotter. This has some initial points,
    and some manually-entered points. These points should be preserved
    without (much) modification. 
    
    The data is in GPX notation because that's what the new chartplotter emits.
    
-   The JSON capture from the legacy chartplotter. This can be transformed
    into GPX format so that it's all consistent.

The merged data is a list of waypoints, in GPX. This is a new file, the
merged waypoints to be uploaded to the new chartplotter to create happy boaters,
and complete the user story. 

What about routes?

They're much easier to deal with. They tend to be much less volatile. A route
modification is (actually) a relatively infrequent event. New routes are a big
deal. Discussed separately.

Process
=======

We have the legacy waypoints on a MicroSD card from the chartplotter.

We have the new waypoints captured on a laptop computer.

The default filenames are wired into the ``waypoint_merge`` application.
It would be good to generalize this to work with other filenames.

::

    PYTHONPATH=. python3 -m nmeatools.waypoint_merge >merged_waypoints.gpx

The output is list of unique waypoints that are copied
back to the MicroSD card for upload.

Example
=======

::

    MacBookPro-SLott:NMEA-Tools slott$ PYTHONPATH=. python3 -m nmeatools.waypoint_merge >merged_waypoints.gpx
    INFO:merge:MASTER
    INFO:merge:UPDATE
    INFO:merge:CHES 59A near 0.0002 Chesapeake 59A
    INFO:merge:GWICO 1 near 0.0002 Great Wicomico 1
    INFO:merge:GWICO 2 near 0.0002 Great Wicomico Light
    ...
    
This shows waypoints in the update file with names like ``'CHES 59A'``
which are very close to existing waypoints with names like ``'Chesapeake 59A'``.
The distance of 0.0002 NM is about 1 foot.

The practical threshold for GPS without careful correction
is 25.6ft, about 7.8m, 95% of the time. We use a wider factor of about 32ft (about 9.7m)
to determine that two waypoints appear to be the same.
