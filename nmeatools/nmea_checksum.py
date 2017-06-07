#!/usr/bin/env python3
"""
Spike for checking NMEA checksum.

$GPxxx messages are widely described.

http://catb.org/gpsd/AIVDM.html describes !AIVDM messages, these use a 6-bit
protocol similar to base-64 encoding.
"""

from functools import reduce
from operator import xor
import doctest
import sys

def validate(aLine):
    """
    >>> validate(b"$GPGSA,A,2,29,19,28,,,,,,,,,,23.4,12.1,20.0*0F")
    [b'GPGSA', b'A', b'2', b'29', b'19', b'28', b'', b'', b'', b'', b'', b'', b'', b'', b'', b'23.4', b'12.1', b'20.0']
    >>> validate(b"$GPGSA,A,2,29,19,28,,,,,,,,,,23.4,")  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
      File "/Library/Frameworks/Python.framework/Versions/3.6/lib/python3.6/doctest.py", line 1330, in __run
        compileflags, 1), test.globs)
      File "<doctest __main__.validate[1]>", line 1, in <module>
        validate(b"$GPGSA,A,2,29,19,28,,,,,,,,,,23.4,")
      File "/Users/slott/Documents/Projects/NMEA-Tools/nmea_checksum.py", line 23, in validate
        assert sentence[0] in b'$!', "Unexpected {} not in ({}, {})".format(sentence[0], b'$', b'!')
    IndexError: index out of range
    >>> validate(b"29,19,28,,,,,,,,,,23.4,12.1,20.0*0F")  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
      File "/Library/Frameworks/Python.framework/Versions/3.6/lib/python3.6/doctest.py", line 1330, in __run
        compileflags, 1), test.globs)
      File "<doctest __main__.validate[2]>", line 1, in <module>
        validate(b"29,19,28,,,,,,,,,,23.4,12.1,20.0*0F")  # doctest: +IGNORE_EXCEPTION_DETAIL
      File "/Users/slott/Documents/Projects/NMEA-Tools/nmea_checksum.py", line 32, in validate
        assert sentence[0] in b'$!', "Unexpected {} not in ({}, {})".format(sentence[0], b'$', b'!')
    AssertionError: Unexpected 50 not in (b'$', b'!')
    
    >>> validate(b'$GPGLL,2542.9243,N,08013.6310,W,162823.000,A*29')
    [b'GPGLL', b'2542.9243', b'N', b'08013.6310', b'W', b'162823.000', b'A']
    """
    sentence, star, checksum = aLine.rpartition(b'*')
    assert sentence[0] in b'$!', f"Unexpected {sentence[0]} not in b'$!'
    if star == b'*':
        cs = reduce(xor, sentence[1:])
        assert int(checksum, 16) == cs
    return sentence[1:].split(b',')

doctest.testmod(verbose=False)
