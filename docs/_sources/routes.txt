#########################
Routes and Route Planning
#########################

This is a more complex consideration.

There are three possible sources for routes, each with it's own unique
requirements.

-   Some routes are more complex and a planned on the laptop using GPSNavX.
    The resulting GPX document can be shared with the new chartplotter 
    via  MicroSD card.
    NMEA data must be pushed to the old chartplotter through the NMEA interface.
    
-   Some routes are planned "on-the-fly" using the chartplotter.
    The GPX can be exported to a MicroSD card. 
    NMEA data can be pushed to the old chartplotter through the NMEA interface.
    
-   It's remotely possible to plan a route on the legacy chartplotter.
    It has a good UX for route planning, and it's very rugged and reliable.
    In this case, the laptop must still be used to capture the route
    and share it.
    
The NMEA push is not (currently) part of the :mod:`nmeatools.nmea_device` module.
