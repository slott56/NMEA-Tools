"""Define NMEA Sentences. 
This lazily builds fields from the source bytes using descriptors
for the individual conversions.

Messages that are captured and (to an extent) parsed. 

- $GPWPL - Waypoint (example: b'3845.363', b'N', b'07629.551', b'W', b'FISHTRP')
- $GPRTE - Route

These are not (currently) interpreted.

- $GPDBT - Depth Below Transducer
- $GPDPT - Depth
- $GPMTW - Water Temperature
- $GPVHW - Water Speed and Heading
- $GPRMC - Recommended Minimum Specific GPS/TRANSIT Data
- $GPGGA - Global Positioning System Fix Data
- $GPGLL - Geographic position, latitude / longitude
- $GPGSA - GPS DOP and active satellites 
- $GPGSV - GPS Satellites in view
- $GPVTG - Track made good and ground speed
- $GPZDA - Date & Time
- $GPXTE - Cross-track error, Measured

Unit Tests
==========

>>> class Sample(Sentence):    
...    f0 = Integer(1, "Item One")
...    f1 = Float(2, "Item Two")
...    @property
...    def f2(self):
...        return self.f0 + self.f1

>>> s1 = Sample(b'Sample', b'1', b'2.3')
>>> s1.f0
1
>>> s1.f1
2.3
>>> s1.f2
3.3

>>> s2 = GPWPL(b'GPWPL', b'5128.62', b'N', b'00027.58', b'W', b'EGLL')
>>> import json
>>> txt = json.dumps(s2.to_json)
>>> print(txt)
{"_class": "GPWPL", "_args": ["GPWPL", "5128.62", "N", "00027.58", "W", "EGLL"]}

>>> obj = json.loads(txt, object_hook=decode)
>>> print(obj)
GPWPL 51°28.62′N 0°27.58′W EGLL
"""

from nmeatools.common import logged, Logging
import json
from collections.abc import Callable

class Field:
    """
    Define a field. Provide the position, a description, and a conversion rule.
    
    The name is there to parallel the ``nmea_data`` Namedtuple implementation.
    
    Subclasses should include conversions directly.
    This can be used with conversion plug-in functions.
    
    ``f = Text(1, "Description")`` is better than 
    
    ``f = Field(1, "Description", "f", text)`` which is better than

    ``f = Field(1, "Description", "f", lambda b: b.decode('ascii'))``
    
    >>> class Sample(Sentence):
    ...     f = Field(1, "title", "f", lambda b: b.decode('ascii'))
    >>> s = Sample(b'Sample', b'text')
    >>> s.f
    'text'
    """
    def __init__(self, position, title, name=None, conversion=lambda x: x):
        self.position = position
        self.function = conversion
        self.description = title
        self.cache = None
        
    @staticmethod
    def transform(func, value):
        return func(value)
    
    def __get__(self, object, class_):
        # print(f"get {object} {class_}")
        if self.cache is None:
            if object is not None:
                func = self.function
                self.cache = self.transform(self.function, object.args[self.position])
        return self.cache

class Text(Field):
    def __init__(self, position, title):
        super().__init__(position, title, conversion=self.text)
    
    @staticmethod
    def text(value):
        """
        >>> Text.text(b'xyz')
        'xyz'
        """
        return value.decode("ascii")

class Integer(Field):
    def __init__(self, position, title):
        super().__init__(position, title, conversion=self.nint)
    
    @staticmethod
    def nint(value):
        """Convert to int or None
    
        >>> Integer.nint(b'')
        >>> Integer.nint(b'123')
        123
        """
        if len(value) == 0:
            return None
        return int(value)

class Float(Field):
    def __init__(self, position, title):
        super().__init__(position, title, conversion=self.nfloat)
    
    @staticmethod
    def nfloat(value):
        """Convert to float or None
    
        >>> Float.nfloat(b'')
        >>> Float.nfloat(b'123.45')
        123.45
        """
        if len(value) == 0:
            return None
        return float(value)

class UTC_Time(Field):
    def __init__(self, position, title):
        super().__init__(position, title, conversion=self.utc_time)
        
    @staticmethod
    def utc_time(source):
        """Convert source bytes to UTC time as (H, M, S) triple
        HHMMSS.000
    
        >>> UTC_Time.utc_time(b'123456.000')
        (12, 34, 56.0)
        """
        if source:
            return int(source[:2]), int(source[2:4]), float(source[4:])
        return None, None, None

class UTC_Date(Field):
    def __init__(self, position, title):
        super().__init__(position, title, conversion=self.utc_date)
        
    @staticmethod
    def utc_date(source):
        """Convert source bytes to UTC date.
        mmddyy

        >>> UTC_Date.utc_date(b'091056')
        (9, 10, 56)
        """
        if source:
            return int(source[:2]), int(source[2:4]), int(source[4:])
        return None, None, None

class LatAngle(Field):
    """Note that the hemisphere information (N/S) isn't present."""
    def __init__(self, position, title):
        super().__init__(position, title, conversion=self.lat)
        
    @staticmethod
    def lat(source):
        """Convert source bytes to latitude (deg, min) pair.
        Latitude: 2543.7024 = DDMM.MMMM
    
        >>> LatAngle.lat(b'2543.7024')
        (25, 43.7024)
        """
        if len(source) == 0: return None, None
        dd= int(source[:2])
        mm= float(source[2:])
        return int(dd), float(mm)

class LonAngle(Field):
    """Note that the hemisphere information (E/W) isn't present."""
    def __init__(self, position, title):
        super().__init__(position, title, conversion=self.lon)
        
    @staticmethod
    def lon(source):
        """Convert source bytes to longitude (deg, min) pair.
        Longitude: 08014.5267 = DDDMM.MMMM
    
        >>> LonAngle.lon(b'08014.5267')
        (80, 14.5267)
        """
        if len(source) == 0: return None, None
        dd= int(source[:3])
        mm= float(source[3:])
        return int(dd), float(mm)

class Latitude(Field):
    """Two source fields are combined: the angle and the hemisphere (N/S)."""
    def __init__(self, pos_angle, pos_h, title):
        self.position = pos_angle, pos_h
        self.description = title
        self.cache = None
        
    def __get__(self, object, class_):
        # print(f"get {object} {class_}")
        if self.cache is None:
            lat_deg, lat_min = LatAngle.lat(object.args[self.pos_angle])
            lat_h = object.args[self.pos_h]
            self.cache = (lat_deg + lat_min/60) * (-1 if lat_h == 'S' else +1)
        return self.cache
        
class Longitude(Field):
    """Two source fields are combined: the angle and the hemisphere (E/W)."""
    def __init__(self, pos_angle, pos_h, title):
        self.position = pos_angle, pos_h
        self.description = title
        self.cache = None
        
    def __get__(self, object, class_):
        # print(f"get {object} {class_}")
        if self.cache is None:
            lon_deg, lon_min = LonAngle.lon(object.args[self.pos_angle])
            lon_h = object.args[self.pos_h]
            self.cache = (lon_deg + lon_min/60) * (-1 if lon_h == 'W' else +1)
        return self.cache

@logged
class Sentence:
    """
    >>> class Sample(Sentence):    
    ...     f0 = Integer(1, "Item One")
    ...     f1 = Float(2, "Item Two")
    ...     @property
    ...     def f2(self):
    ...         return self.f0 + self.f1
    >>> s = Sample(b'Sample', b'1', b'2.3')
    >>> s.f0
    1
    >>> s.f1
    2.3
    >>> s.f2
    3.3
    
    Can be converted from original fields = [...] lists.
        
    >>> class Sample2(Sentence):
    ...     f0 = Field(1, "Item One", "f0", int)
    ...     f1 = Field(2, "Item Two", "f1", float)
    ...     @property
    ...     def f2(self):
    ...         return self.f0 + self.f1
    >>> s = Sample2(b'Sample', b'1', b'2.3')
    >>> s.f0
    1
    >>> s.f1
    2.3
    >>> s.f2
    3.3

    """
    def __init__(self, *args):
        self.args = args
        self._name = self.args[0].decode('ascii')
    def __repr__(self):
        return f"{self.__class__.__name__}(*{self.args!r})"
    @property
    def to_json(self):
        return {
            '_class': self.__class__.__name__, 
            '_args': [a.decode('ascii') for a in self.args]
        }
       
@logged
class Sentence_Factory( Callable ):
    """
    Given a sequence of values, locate the class with a name that
    matches the sentence header and instantiate that class.
    
    This examines all subclasses of :class:`Sentence`. The class names
    must match the sentence header.
    If there's no match, create an :class:`UnknownSentence` instance.
    
    :params args: The message fields. 
    :returns: :class:`Sentence` instance.
    
    >>> sf = Sentence_Factory()
    >>> fields1 = b'GPVTG,59.53,T,,M,0.14,N,0.3,K'.split(b',')
    >>> s1 = sf(*fields1)
    >>> s1
    UnknownSentence(*(b'GPVTG', b'59.53', b'T', b'', b'M', b'0.14', b'N', b'0.3', b'K'))
    
    >>> fields2 = b'GPWPL', b'5128.62', b'N', b'00027.58', b'W', b'EGLL'
    >>> s2 = sf(*fields2)
    >>> s2
    GPWPL 51°28.62′N 0°27.58′W EGLL
    """
    def __init__(self):
        self.sentence_class_map = {
            class_.__name__.encode('ascii'): class_ 
            for class_ in Sentence.__subclasses__()
        }
    def __call__(self, *args):
        self.log.debug(args)
        class_= self.sentence_class_map.get(args[0])
        if class_:
            sentence= class_(*args)
            return sentence
        else:
            self.log.debug(f"Don't recognize {args[0]}")
            return UnknownSentence(*args)
             
@logged
class UnknownSentence(Sentence):
    """Fallback for NMEA0183 Sentences that aren't otherwise parseable.
    """
    pass
    
class GPRTE(Sentence):
    """
    GP Route 
    
    Examples::
    
        $GPRTE,2,1,c,0,PBRCPK,PBRTO,PTELGR,PPLAND,PYAMBU,PPFAIR,PWARRN,PMORTL,PLISMR*73
        $GPRTE,2,2,c,0,PCRESY,GRYRIE,GCORIO,GWERR,GWESTG,7FED*34
               1 2 3 4 5 ..
               
        1. Number of sentences in sequence
        2. Sentence number
        3. 'c' = Current active route, 'w' = waypoint list starts with destination waypoint
        4. Name or number of the active route
        5. Rest of the body is the names of waypoints in Route
    """
    length = Integer(1, "Number of sentences in sequence")
    sentence = Integer(2, "Sentence number")
    status = Text(3, "Current or Waypoint")
    id = Text(4, "Name or Number")
    @property
    def waypoints(self):
        return [name.decode('ascii') for name in self.args[5:]]
    def __repr__( self ):
        return f"{self._name} {self.id!r} {self.sentence} {self.status} {self.waypoints}"

class GPWPL(Sentence):
    """GP Waypoint Location
    
    Examples::
    
        $GPWPL,4917.16,N,12310.64,W,003*65
               1         2          3
               
          1. 4917.16,N    Latitude of waypoint. This is 49°16.17′N
          2. 12310.64,W   Longitude of waypoint. This is 123°10.64′W
          3. 003          Waypoint ID

        $GPWPL,5128.62,N,00027.58,W,EGLL*59
               1       2 3        4 5

          1. 5128.62   Latitude of this waypoint
          2. N         North/South
          3. 00027.58  Longitude of this waypoint
          4. W         East/West
          5. EGLL      Ident of this waypoint
    
    """
    lat_angle = LatAngle(1, "Latitude Angle")
    lat_h = Text(2, "N/S Indicator")
    lon_angle = LonAngle(3, "Longitude Angle")
    lon_h = Text(4, "E/W Indicator")
    name = Text(5, "Name or ID")
    latitude = Latitude(1, 2, "Waypoint latitude degrees")
    longitude = Longitude(3, 4, "Waypoint longitude degrees")
    def __repr__( self ):
        lat_deg, lat_min = self.lat_angle
        lon_deg, lon_min = self.lon_angle
        return (
            f"{self._name} {lat_deg}°{lat_min}′{self.lat_h}"
            f" {lon_deg}°{lon_min}′{self.lon_h} {self.name}"
            )
            
def decode(object):
    if set(object.keys()) == {'_class', '_args'}:
        # Mock sentence factory...
        class_ = eval(object['_class'])
        return class_(*[a.encode('ascii') for a in object['_args']])
    return object

import doctest
doctest.testmod(verbose=False)


