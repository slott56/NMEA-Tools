"""
Data Capture Demo
"""
from nmeatools.nmea_device import Listener
#from nmeatools.nmea_data_eager import Sentence_Factory
from nmeatools.nmea_data_lazy import Sentence_Factory
from nmeatools.common import logged, Logging

from types import SimpleNamespace
import sys
import logging
from collections import Counter
from pprint import pprint

def sample_CP(listener):
    """
    Chart Plotter. The background message cycle is filtered out. Reads until Ctrl-C.
    """
    background = ('GPXTE', 'GPRMC', 'GPDBT', 'GPDPT', 'GPMTW', 'GPVHW', 'GPGGA', 'GPGLL')
    counts = Counter()
    sentence_factory= Sentence_Factory()
    try:
        for sentence_fields in listener:
            sentence= sentence_factory(*sentence_fields)
            if sentence._name not in background:
                print(repr(sentence._name), sentence)
                text = Encoder().encode(sentence)
                print(text)
            counts[sentence._name] += 1
    except KeyboardInterrupt:
        pprint(counts)

def sample_GPS(listener, limit=16):
    """
    GPS. Displays selected messages until some limit is reached.
    """
    counts = Counter()
    sentence_factory= Sentence_Factory()
    for sentence_fields in listener:
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
        with Listener(device) as listener:
            sample_GPS(listener, limit=16)

