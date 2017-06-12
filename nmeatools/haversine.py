"""Haversine computation.

Defines a handy function for distance in Nautical Miles.

..  function:: nm_haversine(lat_1, lon_1, lat_2, lon_2)
    
    Computes distance in NM
    
    :param lat_1: Latitude of point 1
    :param lon_1: Longitude of point 1
    :param lat_2: Latitude of point 2
    :param lon_2: Longitude of point 2
    :returns: distance, NM
"""
from math import radians, sin, cos, sqrt, asin
from functools import partial

MI= 3959
NM= 3440
KM= 6373

def haversine(lat_1: float, lon_1: float,
    lat_2: float, lon_2: float, R: float=NM) -> float:
    """Distance between points.
    
    ..  math::
        
        a = \\sqrt { \\sin^2(\\frac{\\Delta_{lat}}{2}) + \\cos(lat_1) \\cos(lat_2) \\sin^2(\\frac{\\Delta_{lon}}{2}) }
        
    ..  math::
    
        c = 2R \\arcsin{a}

    R is radius, R=MI computes in miles. Default is nautical miles.
    
    :param lat_1: Latitude of point 1
    :param lon_1: Longitude of point 1
    :param lat_2: Latitude of point 2
    :param lon_2: Longitude of point 2
    :param R: Mean earth radius in desired units. R=NM is the default.
    :returns: distance based on units of R.

    >>> round(haversine(36.12, -86.67, 33.94, -118.40, R=6372.8), 5)
    2887.25995
    """
    Δ_lat = radians(lat_2) - radians(lat_1)
    Δ_lon = radians(lon_2) - radians(lon_1)
    lat_1 = radians(lat_1)
    lat_2 = radians(lat_2)

    a = sqrt(sin(Δ_lat/2)**2 + cos(lat_1)*cos(lat_2)*sin(Δ_lon/2)**2)
    c = 2*asin(a)

    return R * c

nm_haversine = partial(haversine, R=NM)

__test__ = {
    'partial': '''\
>>> round(nm_haversine(36.12, -86.67, 33.94, -118.40), 2)
1558.53
''',
}

if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=2)
