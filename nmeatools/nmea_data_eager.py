#!/usr/bin/env python3
"""Define NMEA Sentences. 
This eagerly populates many fields from the source bytes.

Messages that are captured and (to an extent) parsed. 

- $GPRMC - Recommended Minimum Specific GPS/TRANSIT Data
- $GPGGA - Global Positioning System Fix Data
- $GPGLL - Geographic position, latitude / longitude
- $GPGSA - GPS DOP and active satellites 
- $GPGSV - GPS Satellites in view
- $GPVTG - Track made good and ground speed
- $GPZDA - Date & Time
- $GPXTE - Cross-track error, Measured
- $GPWPL - Waypoint (example: b'3845.363', b'N', b'07629.551', b'W', b'FISHTRP')
- $GPRTE - Route

These are not (currently) interpreted.

- $GPDBT - Depth Below Transducer
- $GPDPT - Depth
- $GPMTW - Water Temperature
- $GPVHW - Water Speed and Heading

"""
from nmeatools.common import logged, Logging

import time
from pprint import pprint, pformat
from collections import Callable, namedtuple
import logging
import sys
import datetime
from json import JSONEncoder, JSONDecoder

def text( source ):
    """Convert source bytes to text.

    >>> text(b'xyz')
    'xyz'
    """
    return source.decode('ascii')

def utc_time(source):
    """Convert source bytes to UTC time as (H, M, S) triple
    HHMMSS.000
    
    >>> utc_time(b'123456.000')
    (12, 34, 56.0)
    """
    if source:
        return int(source[:2]), int(source[2:4]), float(source[4:])
    return None, None, None

def utc_date(source):
    """Convert source bytes to UTC date.
    mmddyy

    >>> utc_date(b'091056')
    (9, 10, 56)
    """
    if source:
        return int(source[:2]), int(source[2:4]), int(source[4:])
    return None, None, None

def lat(source):
    """Convert source bytes to a latitude (deg, min) pair.
    Latitude: 2543.7024 = DDMM.MMMM
    
    >>> lat(b'2543.7024')
    (25, 43.7024)
    """
    if len(source) == 0: return None, None
    dd= int(source[:2])
    mm= float(source[2:])
    return int(dd), float(mm)

def lon(source):
    """Convert source bytes to longitude (deg, mim) pair.
    Longitude: 08014.5267 = DDDMM.MMMM
    
    >>> lon(b'08014.5267')
    (80, 14.5267)
    """
    if len(source) == 0: return None, None
    dd= int(source[:3])
    mm= float(source[3:])
    return int(dd), float(mm)

def nfloat(source):
    """Convert to float or None
    
    >>> nfloat(b'')
    >>> nfloat(b'123.45')
    123.45
    """
    if len(source) == 0: return None
    return float(source)

def nint(source):
    """Convert to int or None
    
    >>> nint(b'')
    >>> nint(b'123')
    123
    """
    if len(source) == 0: return None
    return int(source)
    
# Define each field to be decoded from the message.
Field = namedtuple('Field', ['title', 'name', 'conversion'])

@logged
class Sentence:
    """Superclass for NMEA0183 Sentences.
        
    Each subclass provides a value for ``fields``.
    This sequence if :class:`Field` objects is used to convert the items in the 
    message from bytes to useful values.
    
    There are two fields common to all sentences.
    
    :_name:
        The sentence type as text. The bytes are decoded from ASCII.
    :_args:
        The tuple with the original argument values as Python text.
        These have been decoded from ASCII, which is (perhaps) not the best
        idea, but it makes access simple. 
    """
    fields= []  # Sequence of Field definitions.
    def __init__( self, *args ):
        """Generic sentence creation.
        
        1. Save the name and args.
        
        2. Examine each field and apply the conversion function to set additional attributes.
        """
        self._name= args[0].decode('ascii')
        self._args = [arg.decode('ascii') for arg in args[1:]]
        for field, arg in zip(self.fields, args[1:]):
            try:
                setattr(self, field.name, field.conversion(arg))
            except ValueError as e:
                self.log.error(f"{e} {field.title} {field.name} {field.conversion} {arg}")

    def __repr__( self ):
        value = pformat(self.__dict__)
        return f"{self._name} {value}"

@logged
class UnknownSentence(Sentence):
    """Fallback for NMEA0183 Sentences that aren't otherwise parseable.
    """
    def __repr__( self ):
        return f"{self._name} {self._args}"

class GPRMC(Sentence):
    """Position and time"""
    fields = [
        Field('UTC Time', 'time_utc', utc_time),
        Field('Status', 'status', text),
        Field('Latitude', 'lat', lat),
        Field('N/S Indicator', 'lat_h', text),
        Field('Longitude', 'lon', lon),
        Field('E/W Indicator', 'lon_h', text),
        Field('Speed over ground', 'sog', nfloat),
        Field('Course over ground', 'cog', nfloat),
        Field('UTC Date', 'date_utc', utc_date),
        Field('Magnetic variation', 'mag_var', nfloat),
        Field('Magnetic variation', 'mag_var_flag', text),
    ]
    def __init__(self, *args):
        super().__init__(*args)
        # Calculate proper UTC date/time
        dd, mm, yy = self.date_utc
        HH, MM, SS = self.time_utc
        if dd and mm and yy and HH and MM and SS:
            self.utc = datetime.datetime(2000+yy, mm, mm, HH, MM, int(SS))
        else:
            self.utc = None
        self.lat_deg, self.lat_min = self.lat
        self.lon_deg, self.lon_min = self.lon
    def __repr__( self ):
        return (
            f"{self._name} {self.utc:%H:%M:%S} {self.lat_deg}°{self.lat_min}′{self.lat_h}"
            f" {self.lon_deg}°{self.lon_min}′{self.lon_h} SOG {self.sog} COG {self.cog}"
            )

class GPGGA(Sentence):
    """Fix data"""
    fields = [
        Field('UTC Time', 'time_utc', utc_time),
        Field('Latitude', 'lat', lat),
        Field('N/S Indicator', 'lat_h', text),
        Field('Longitude', 'lon', lon),
        Field('E/W Indicator', 'lon_h', text),
        Field('Position Fix', 'fix', text),
        Field('Satellites Used', 'sat_used', nint),
        Field('Horizontal dilution of precision (HDOP)', 'hdop', nfloat),
        Field('Altitude in meters according to WGS-84 ellipsoid', 'alt', nfloat),
        Field('Altitude Units', 'units_alt', text),
        Field('Geoid seperation in meters according to WGS-84 ellipsoid', 'geoid_sep', nfloat),
        Field('Seperation Units', 'units_sep', text),
        Field('Age of DGPS data in seconds', 'age', nfloat),
        Field('DGPS Station ID', 'station', text),
        ]
    # Position Fix codes:
    #     0 = Invalid;
    #     1 = Valid SPS;
    #     2 = Valid DGPS;
    #     3 = Valid PPS.
    def __init__( self, *args ):
        super().__init__( *args )
        HH, MM, SS = self.time_utc
        if HH and MM and SS:
            self.utc = datetime.time(HH, MM, int(SS))
        else:
            self.utc = None
        self.lat_deg, self.lat_min = self.lat
        self.lon_deg, self.lon_min = self.lon
    def __repr__( self ):
        return (
            f"{self._name} {self.utc} {self.lat_deg}°{self.lat_min}′{self.lat_h}"
            f" {self.lon_deg}°{self.lon_min}′{self.lon_h} Fix {self.fix} Sats {self.sat_used}"
            )

class GPGLL(Sentence):
    """Position"""
    fields = [
        Field('Latitude', 'lat', lat),
        Field('N/S Indicator', 'lat_h', text),
        Field('Longitude', 'lon', lon),
        Field('E/W Indicator', 'lon_h', text),
        Field('UTC Time', 'time_utc', utc_time),
        Field('Status', 'status', text),
        ]
    # Status Codes:
    # A = valid, V = invalid
    def __init__( self, *args ):
        super().__init__( *args )
        HH, MM, SS = self.time_utc
        if HH and MM and SS:
            self.utc= datetime.time(HH, MM, int(SS))
        else:
            self.utc = None
        self.lat_deg, self.lat_min = self.lat
        self.lon_deg, self.lon_min = self.lon
        self.valid= "Valid" if self.status == "A" else "Invalid"
    def __repr__( self ):
        return (
            f"{self._name} {self.utc} {self.lat_deg}°{self.lat_min}′{self.lat_h}"
            f" {self.lon_deg}°{self.lon_min}′{self.lon_h} {self.valid}"
            )

class GPGSA(Sentence):
    """Active satellites"""
    fields= [
        Field('Mode 1', 'mode1', text), # M = Forced 2D/3D, A = Auto 2D/3D
        Field('Mode 2', 'mode2', text), # 1 = No fix, 2 = 2D, 3 = 3D
        Field('Satellite used on channel PRN', 'prn_00', text),
        Field('PRN01', 'prn_01', text),
        Field('PRN02', 'prn_02', text),
        Field('PRN03', 'prn_03', text),
        Field('PRN04', 'prn_04', text),
        Field('PRN05', 'prn_05', text),
        Field('PRN06', 'prn_06', text),
        Field('PRN07', 'prn_07', text),
        Field('PRN08', 'prn_08', text),
        Field('PRN09', 'prn_09', text),
        Field('PRN10', 'prn_10', text),
        Field('PRN11', 'prn_11', text),
        Field('Position dilution of precision (PDOP)', 'pdop', nfloat),
        Field('Horizontal dilution of precision (HDOP)', 'hdop', nfloat),
        Field('Vertical dilution of precision (VDOP)', 'vdop', nfloat),
        ]

class GPGSV(Sentence):
    """Satellites in view"""
    fields= [
        Field('Number of messages (1 to 9)', 'num', nint),
        Field('Sequence number', 'seq', nint),
        Field('Satellites in view', 'satinview', nint),
        Field('Satellite ID 1 (1-32)', 'sat1_id', nint),
        Field('Elevation in degrees (0-90)', 'sat1_el', nint),
        Field('Azimuth in degrees (0-359)', 'sat1_az', nint),
        Field('Signal to noise ration in dBHZ (0-99)', 'sat1_sn', nint),
        Field('Satellite ID 2 (1-32)', 'sat2_id', nint),
        Field('Elevation in degrees (0-90)', 'sat2_el', nint),
        Field('Azimuth in degrees (0-359)', 'sat2_az', nint),
        Field('Signal to noise ration in dBHZ (0-99)', 'sat2_sn', nint),
        Field('Satellite ID 3 (1-32)', 'sat3_id', nint),
        Field('Elevation in degrees (0-90)', 'sat3_el', nint),
        Field('Azimuth in degrees (0-359)', 'sat3_az', nint),
        Field('Signal to noise ration in dBHZ (0-99)', 'sat3_sn', nint),
        Field('Satellite ID 4 (1-32)', 'sat4_id', nint),
        Field('Elevation in degrees (0-90)', 'sat4_el', nint),
        Field('Azimuth in degrees (0-359)', 'sat4_az', nint),
        Field('Signal to noise ration in dBHZ (0-99)', 'sat4_sn', nint),
    ]

class GPVTG(Sentence):
    """Course over ground"""
    fields= [
        Field('Course in degrees', 'course_1', nfloat),
        Field('Reference, T = True heading', 'ref_1', text),
        Field('Course in degrees', 'course_2', nfloat),
        Field('Reference, M = Magnetic heading', 'ref_2', text),
        Field('Horizontal speed (SOG)', 'sog_1', nfloat),
        Field('Units, N = Knots', 'units_sog_1', text),
        Field('Horizontal Speed (SOG)', 'sog_2', nfloat),
        Field('Units, К = Km/h', 'units_sog_2', text),
    ]

class GPZDA(Sentence):
    """UTC Date and Time"""
    fields= [
        Field('UTC Time', 'time_utc', utc_time),
        Field('Day (01 to 31)', 'day', nint),
        Field('Month (01 to 12)', 'month', nint),
        Field('Year', 'year', nint),
        Field('Time zone, GMT displacement, hours (00 to ± 13)', 'tz_hr', nint),
        Field('Time zone, GMT displacement, minutes', 'tz_min', nint),
    ]

class GPXTE(Sentence):
    """Cross-Track Error, Measured"""
    fields = [
        Field("General warning flag", "warning", text),
        Field("Not Used", "not_used", text),
        Field("cross track error distance", "distance", nfloat),
        Field("steer to correct (L/R)", "steer", text),
        Field("Units N = Nautical miles", "units", text),
    ]

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
    fields = [
        Field('Latitude', 'lat_src', lat),
        Field('N/S Indicator', 'lat_h', text),
        Field('Longitude', 'lon_src', lon),
        Field('E/W Indicator', 'lon_h', text),
        Field("Name", "name", text),        
    ]
    def __init__( self, *args ):
        super().__init__( *args )
        self.lat_deg, self.lat_min = self.lat_src
        self.lon_deg, self.lon_min = self.lon_src
        lat_sign = 1 if self.lat_h.upper() == "N" else -1
        self.latitude = lat_sign * (float(self.lat_deg)+float(self.lat_min)/60)
        lon_sign = 1 if self.lon_h.upper() == "E" else -1
        self.longitude = lon_sign * (float(self.lon_deg)+float(self.lon_min)/60)
    def __repr__( self ):
        return (
            f"{self._name} {self.lat_deg}°{self.lat_min}′{self.lat_h}"
            f" {self.lon_deg}°{self.lon_min}′{self.lon_h} {self.name}"
            )

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
    fields = [
        Field("Number of sentences in sequence", 'length', nint),
        Field("Sentence number", "sentence", nint),
        Field("Current or Waypoint", "status", text),
        Field("Name or Number", "id", text),
    ]
    def __init__( self, *args ):
        super().__init__( *args )
        self.waypoints = self._args[5:]
    def __repr__( self ):
        return f"{self._name} {self.id!r} {self.sentence} {self.status} {self.waypoints}"
        
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
    >>> fields = b'GPVTG,59.53,T,,M,0.14,N,0.3,K'.split(b',')
    >>> s = sf(*fields)
    >>> s
    GPVTG {'_args': ['59.53', 'T', '', 'M', '0.14', 'N', '0.3', 'K'],
     '_name': 'GPVTG',
     'course_1': 59.53,
     'course_2': None,
     'ref_1': 'T',
     'ref_2': 'M',
     'sog_1': 0.14,
     'sog_2': 0.3,
     'units_sog_1': 'N',
     'units_sog_2': 'K'}
     
    """
    sentence_class_map = {
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
class Encoder(JSONEncoder):
    """
    Encode the sentence into JSON. This dumps the raw ``_args`` value, 
    ignoring all derived values.  This allows a change to the class definition;
    when the JSON is decoded, additional or different values will be created
    from the original raw data.
    
    Note that the JSON document doesn't **really** work in bytes. We had two
    choices: base64 encode the original bytes, or trust that the bytes were only
    a subset of printable ASCII characters that overlap with UTF-8.
    
    We chose the latter approach. The output is text, which overlaps with ASCII.
    This allows the :class:`Sentence_Factory` and the various subclasses
    of :class:`Sentence` to use text internally.
        
    >>> object = GPWPL(b'GPWPL',b'5128.62',b'N',b'00027.58',b'W',b'EGLL')
    >>> object
    GPWPL 51°28.62′N 0°27.58′W EGLL
    >>> text = Encoder(sort_keys=True, indent=2).encode(object)
    >>> print(text)
    {
      "_args": [
        "5128.62",
        "N",
        "00027.58",
        "W",
        "EGLL"
      ],
      "_class": "GPWPL",
      "_name": "GPWPL"
    }

    """
    def default(self, obj):
        if isinstance(obj, Sentence):
            as_dict = dict(
                _class=obj.__class__.__name__,
                _name=obj._name,
                _args=obj._args
            )
            return as_dict
        else:
            return super().default(obj)

class Decoder(JSONDecoder):
    """
    Decode a sentence from JSON notation. This re-applies the class definition,
    computing and derived values from the original bytes.
    
    Note that the JSON document doesn't **really** work in bytes. We had two
    choices: base64 encode the original bytes, or trust that the bytes were only
    a subset of printable ASCII characters that overlap with UTF-8.
    
    We chose the latter approach. The input is text, which overlaps with ASCII.
    We need to encode it into ASCII to recover the bytes. These are then passed
    to the :class:`Sentence_Factory` to recover :class:`Sentence` instances.
    
    >>> object = GPWPL(b'GPWPL',b'5128.62',b'N',b'00027.58',b'W',b'EGLL')
    >>> object
    GPWPL 51°28.62′N 0°27.58′W EGLL
    >>> text = Encoder().encode(object)
    >>> new_object = Decoder().decode(text)
    >>> new_object
    GPWPL 51°28.62′N 0°27.58′W EGLL
    """
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw, object_hook=self.nmea_object_hook)
        
    def nmea_object_hook(self, as_dict):
        if '_class' in as_dict:
            # Should be Sentence_Factory() instance.
            class_ = eval(as_dict['_class'])
            # Items must be built from bytes. True fact.
            return class_(as_dict['_name'].encode('ascii'), *[v.encode('ascii') for v in as_dict['_args']])
        else:
            return super().object_hook(as_dict)

import doctest
doctest.testmod(verbose=False)
