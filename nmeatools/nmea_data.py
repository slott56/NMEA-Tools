#!/usr/bin/env python3
"""Read NMEA messages via a NMEA to USB interface.
This includes GPS antennas like BU-353 and Standard Horizon CP300i Chart Plotter.

Here's an example of NMEA 0183 to USB hardware.

http://www.digitalyachtamerica.com/index.php/en/products/interfacing/nmeausb/product/67-usb-to-nmea-adaptor

PySerial is required. Using PySerial 3.3.
https://pypi.python.org/pypi/pyserial

Typical interface to NMEA 0183 requires this kind of serial interface:

-   Typical Baud rate	4800
-   Data bits	8
-   Parity	None
-   Stop bits	1
-   Handshake	None

We'll decode NMEA 0183 Sentences. See http://www.robosoft.info/en/technologies/knowledgebase/nmea0183

The checksum is the bitwise exclusive OR of ASCII codes of all characters between the $ and \*.
This is done with ``reduce(operator.xor, bytes)``

See http://en.wikipedia.org/wiki/NMEA_0183

See http://www.gpsinformation.org/dale/nmea.htm#nmea

See http://freenmea.net/docs

See http://www.catb.org/gpsd/NMEA.html

See https://www.sparkfun.com/datasheets/GPS/NMEA%20Reference%20Manual1.pdf

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

Unit Test
==========

Note the subtle complexity of passing end-of-line in a string to doctest.
We can't simply use ``\r\n`` in a sample input string, or the compiler being
used by doctest gets confused.

Good Messages:

>>> m0= b'''$GPRMC,162823.000,A,2542.9243,N,08013.6310,W,0.14,59.53,180214,,*2F\r
... '''
>>> m1= b'''$GPVTG,59.53,T,,M,0.14,N,0.3,K*5C\r
... '''
>>> m2= b'''$GPGGA,162824.000,2542.9243,N,08013.6311,W,1,06,1.5,3.3,M,-27.3,M,,0000*6E\r
... '''
>>> m3= b'''$GPGLL,2542.9243,N,08013.6310,W,162823.000,A*29\r
... '''
>>> m4= b'''$GPGSA,A,3,29,24,18,14,22,27,,,,,,,2.9,1.5,2.5*3E\r
... '''
>>> m5= b'''$GPGSV,3,1,10,21,82,249,18,24,54,090,37,18,52,343,33,15,32,039,34*7D\r
... '''
>>> m6= b'''$GPGSV,3,2,10,14,28,244,36,22,27,307,33,29,12,190,32,06,10,293,28*74\r
... '''
>>> m7= b'''$GPGSV,3,3,10,27,08,303,27,12,00,139,25*7F\r
... '''
>>> Scanner.validate(m0)
(b'GPRMC', b'162823.000', b'A', b'2542.9243', b'N', b'08013.6310', b'W', b'0.14', b'59.53', b'180214', b'', b'')
>>> Scanner.validate(m1)
(b'GPVTG', b'59.53', b'T', b'', b'M', b'0.14', b'N', b'0.3', b'K')
>>> Scanner.validate(m2)
(b'GPGGA', b'162824.000', b'2542.9243', b'N', b'08013.6311', b'W', b'1', b'06', b'1.5', b'3.3', b'M', b'-27.3', b'M', b'', b'0000')
>>> Scanner.validate(m4)
(b'GPGSA', b'A', b'3', b'29', b'24', b'18', b'14', b'22', b'27', b'', b'', b'', b'', b'', b'', b'2.9', b'1.5', b'2.5')
>>> Scanner.validate(m5)
(b'GPGSV', b'3', b'1', b'10', b'21', b'82', b'249', b'18', b'24', b'54', b'090', b'37', b'18', b'52', b'343', b'33', b'15', b'32', b'039', b'34')
>>> Scanner.validate(m6)
(b'GPGSV', b'3', b'2', b'10', b'14', b'28', b'244', b'36', b'22', b'27', b'307', b'33', b'29', b'12', b'190', b'32', b'06', b'10', b'293', b'28')
>>> Scanner.validate(m7)
(b'GPGSV', b'3', b'3', b'10', b'27', b'08', b'303', b'27', b'12', b'00', b'139', b'25')

Broken Message, typical case:

>>> b0= b'''42.9243,N,08013.6310,W,0.14,59.53,180214,,*2F\r
... '''
>>> x= Scanner.validate(b0)  # doctest: +IGNORE_EXCEPTION_DETAIL
Traceback (most recent call last):
  File "/Library/Frameworks/Python.framework/Versions/3.6/lib/python3.6/doctest.py", line 1330, in __run
    compileflags, 1), test.globs)
  File "<doctest __main__[16]>", line 1, in <module>
    x= Scanner.validate(b0)
  File "gps_spike.py", line 143, in validate
    assert sentence_bytes.startswith(b'$'), "Sentence Fragment"
AssertionError: Sentence Fragment

"""

import serial
import time
from types import SimpleNamespace
from pprint import pprint, pformat
from collections import Callable, Counter, namedtuple
from contextlib import closing
import logging
import sys
import datetime
from functools import reduce
from operator import xor
from json import JSONEncoder, JSONDecoder
from nmeatools.common import logged, Logging

@logged
class Scanner:
    """Scan the device, yielding a sequence of sentences.
    
    This is an Interable and a Context Manager for reading from an NMEA-0183 device.
    
    The typical use case is this
    
    ::
    
        with Scanner(options) as GPS:
            for sentnce in GPS:
                print(sentence)
    """
    def __init__(self, options):
        """Create the scanner instance.
        
        :param options: Namespace with options to control serial interface.
            :port: The name of the device, typically /dev/cu.usbserial-A6009TFG
            :baud: The BAUD rate, 4800 is standard.
            :timeout: A timeout. Most talkers will produce messages constantly, and
                this can be as short as 2 seconds.
        """
        self.options = options
        self.device = None
        
    def __enter__(self):
        self.device = serial.Serial(self.options.port, self.options.baud, timeout=self.options.timeout)
        self.log.debug(f"Device: {self.device}")
        return self
        
    def __exit__(self, *exc):
        self.device.close()
        self.device = None
        
    def __iter__(self):
        return self
        
    def __next__(self):
        """Get a line, validate it for completeness, and split into into fields.
        If the message is valid, the yields a tuple of bytes.
        """
        content = None
        while not content:
            sentence_bytes = self.device.readline().rstrip()
            self.log.debug(f"sentence_bytes = {sentence_bytes!r}")
            while not sentence_bytes:
                self.log.error("Timeout")
                sentence_bytes = self.device.readline().rstrip()
            try:
                content = Scanner.validate(sentence_bytes)
            except AssertionError as e:
                self.log.error(f"{e}: {sentence_bytes!r}")
        return content
                
    @staticmethod
    def validate(sentence_bytes):
        """Validate an NMEA sentence, returning either a tuple of substrings or an 
        :exc:`AssertionError`.
        
        :param sentence_bytes: A bytes object with the raw sentence.
        :returns: tuple with individual fields, suitable for use with a
            :class:`Sentence_Factory` isntance.
        :raises AssertionError: If the sentence is incomplete in some way.
        """
        assert sentence_bytes.startswith(b'$'), "Sentence fragment"
        content, _, checksum_txt = sentence_bytes[1:].partition(b"*")
        if checksum_txt:
            checksum_exp = int(checksum_txt, 16)
            checksum_act = reduce(xor, content)
            assert checksum_exp == checksum_act, "Invalid checksum"
        return tuple(content.split(b','))


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
    """Convert source bytes to UTC latitude.
    Latitude: 2543.7024 = DDMM.MMMM
    
    >>> lat(b'2543.7024')
    (25, 43.7024)
    """
    if len(source) == 0: return None, None
    dd= int(source[:2])
    mm= float(source[2:])
    return int(dd), float(mm)

def lon(source):
    """Convert source bytes to UTC longitude.
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
        self.lat = lat_sign * (float(self.lat_deg)+float(self.lat_min)/60)
        lon_sign = 1 if self.lon_h.upper() == "E" else -1
        self.lon = lon_sign * (float(self.lon_deg)+float(self.lon_min)/60)
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
            class_ = eval(as_dict['_class'])
            # Items must be built from bytes. True fact.
            return class_(as_dict['_name'].encode('ascii'), *[v.encode('ascii') for v in as_dict['_args']])
        else:
            return super().object_hook(as_dict)
            
def sample_CP(device):
    """
    Chart Plotter. The background message cycle is filtered out. Reads until Ctrl-C.
    """
    background = ('GPXTE', 'GPRMC', 'GPDBT', 'GPDPT', 'GPMTW', 'GPVHW', 'GPGGA', 'GPGLL')
    counts = Counter()
    sentence_factory= Sentence_Factory()
    try:
        with Scanner(device) as GPS:
            for sentence_fields in GPS:
                sentence= sentence_factory(*sentence_fields)
                if sentence._name not in background:
                    print(repr(sentence._name), sentence)
                    text = Encoder().encode(sentence)
                    print(text)
                counts[sentence._name] += 1
    except KeyboardInterrupt:
        pprint(counts)

def sample_GPS(device, limit=16):
    """
    GPS. Displays selected messages until some limit is reached.
    """
    counts = Counter()
    sentence_factory= Sentence_Factory()
    with Scanner(device) as GPS:
        for sentence_fields in GPS:
            counts['lines'] += 1
            sentence= sentence_factory(*sentence_fields)
            counts[sentence._name] += 1
            if sentence._name in ('GPRMC', 'GPGGA', 'GPGLL'):
                counts['print'] += 1
                print( sentence )
            else:
                counts['skip'] += 1
            limit -= 1
            if limit == 0:
                break
    pprint(counts)

import doctest
doctest.testmod(verbose=False)

if __name__ == "__main__":    
    BU_353_Antenna = SimpleNamespace(
        port = "/dev/cu.usbserial",
        baud = 4800,
        timeout = 2,
    )
    CP300i = SimpleNamespace(
        port = "/dev/cu.usbserial-A6009TFG",
        baud = 4800,
        timeout = 2,
    )

    with Logging(stream=sys.stderr, level=logging.INFO):
        # sample_GPS(BU_353_Antenna, limit=16)
        sample_CP(CP300i)

