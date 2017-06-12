"""
Listener to NMEA interface.

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

The listener is an Interator as well as a Context Manager.

Also -- since messages are ","-separated, it handles the split operation.

Reference
=========

See http://en.wikipedia.org/wiki/NMEA_0183

See http://www.gpsinformation.org/dale/nmea.htm#nmea

See http://freenmea.net/docs

See http://www.catb.org/gpsd/NMEA.html

See https://www.sparkfun.com/datasheets/GPS/NMEA%20Reference%20Manual1.pdf


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
>>> Listener.validate(m0)
(b'GPRMC', b'162823.000', b'A', b'2542.9243', b'N', b'08013.6310', b'W', b'0.14', b'59.53', b'180214', b'', b'')
>>> Listener.validate(m1)
(b'GPVTG', b'59.53', b'T', b'', b'M', b'0.14', b'N', b'0.3', b'K')
>>> Listener.validate(m2)
(b'GPGGA', b'162824.000', b'2542.9243', b'N', b'08013.6311', b'W', b'1', b'06', b'1.5', b'3.3', b'M', b'-27.3', b'M', b'', b'0000')
>>> Listener.validate(m4)
(b'GPGSA', b'A', b'3', b'29', b'24', b'18', b'14', b'22', b'27', b'', b'', b'', b'', b'', b'', b'2.9', b'1.5', b'2.5')
>>> Listener.validate(m5)
(b'GPGSV', b'3', b'1', b'10', b'21', b'82', b'249', b'18', b'24', b'54', b'090', b'37', b'18', b'52', b'343', b'33', b'15', b'32', b'039', b'34')
>>> Listener.validate(m6)
(b'GPGSV', b'3', b'2', b'10', b'14', b'28', b'244', b'36', b'22', b'27', b'307', b'33', b'29', b'12', b'190', b'32', b'06', b'10', b'293', b'28')
>>> Listener.validate(m7)
(b'GPGSV', b'3', b'3', b'10', b'27', b'08', b'303', b'27', b'12', b'00', b'139', b'25')

Broken Message, typical case:

>>> b0= b'''42.9243,N,08013.6310,W,0.14,59.53,180214,,*2F\r
... '''
>>> x= Listener.validate(b0)  # doctest: +IGNORE_EXCEPTION_DETAIL
Traceback (most recent call last):
  File "/Library/Frameworks/Python.framework/Versions/3.6/lib/python3.6/doctest.py", line 1330, in __run
    compileflags, 1), test.globs)
  File "<doctest __main__[16]>", line 1, in <module>
    x= Scanner.validate(b0)
  File "gps_spike.py", line 143, in validate
    assert sentence_bytes.startswith(b'$'), "Sentence Fragment"
AssertionError: Sentence Fragment

"""
from nmeatools.common import logged, Logging

from types import SimpleNamespace
from functools import reduce
from operator import xor
import sys
import logging

import serial

@logged
class Listener:
    """Listen to the device, yielding a sequence of sentences.
    
    This is an Interable and a Context Manager for listening to an NMEA-0183 device.
    
    The typical use case is this
    
    ::
    
        with Listener(options) as GPS:
            for sentnce in GPS:
                print(sentence)
    """
    def __init__(self, options):
        """Create the Listener instance.
        
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
                content = Listener.validate(sentence_bytes)
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

    device = BU_353_Antenna
    with Logging(stream=sys.stderr, level=logging.INFO):
        with Listener(device) as GPS:
            for sentence_fields in GPS:
                print(sentence_fields)
