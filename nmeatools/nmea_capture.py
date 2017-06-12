#!/usr/bin/env python3
"""Capture Waypoints or Routes from Chart Plotter.

..  program:: nmea_capture

::

    usage: nmea_capture.py [-h] [--output OUTPUT] [--baud BAUD]
                           [--timeout TIMEOUT]
                           input


Arguments
=========

..  option:: input

    The device to monitor. Usually ``/dev/cu.usbserial-A6009TFG``

Options
=======

..  option:: -h, --help

    show this help message and exit

..  option:: --output OUTPUT, -o OUTPUT

    The file to write the captured NMEA data to. This will be in JSON
    format and can be used by :program:`waypoint_to_gpx`.

..  option:: --baud BAUD

    BAUD setting, default is 4800

..  option:: --timeout TIMEOUT

    Timeout setting, default is 2 seconds

Description
===========

This an an interactive exercise between the computer capturing the data
and the chartplotter producing the data.

..  csv-table::

    Chartplotter,This App
    1. Start chart plotter.,
    2. Navigate to Waypoints or Route send operation.,
    ,"3. Start capture.\\n``python3 nmeatools.nmea_capture -o data /dev/cu.usbserial-A6009TFG``"
    4. Start Send.,Watch ``.`` and ``+`` to confirm receipt.
    ,"5. Stop capture, saving the file. ``^C``"

"""

from nmeatools.nmea_data_eager import Sentence_Factory, Encoder
from nmeatools.nmea_device import Listener
from nmeatools.common import logged, Logging

import argparse
import sys
from pathlib import Path
from types import SimpleNamespace
from collections import Counter
import logging

logger = logging.getLogger(__name__)

def sentence_iter(options):
    """
    Filtered reader of sentnces. Rejects any sentences from the background list.
    
    Currently, the reject list is::
    
        ('GPRMC', 'GPGGA', 'GPGLL', 'GPGSA', 'GPGSV', 'GPVTG', 'GPZDA', 'GPXTE')
     
    :param options: Options namespace, must have the following items.
        :input: the mounted device, often /dev/cu.usbserial-A6009TFG
        :baud: the baud rate to use, generally 4800
        :timeout: the timeout, generally 2 seconds
    :returns: yields individual sentences that are not in a list of
        background messages.
    """
    background = ('GPRMC', 'GPGGA', 'GPGLL', 'GPGSA', 'GPGSV', 'GPVTG', 'GPZDA', 'GPXTE')
    bg_count = fg_count = 0
    device = SimpleNamespace(
        port=options.input,
        baud=options.baud,
        timeout=options.timeout)
    sentence_factory= Sentence_Factory()
    try:
        with Listener(device) as plotter:
            for sentence_fields in plotter:
                sentence= sentence_factory(*sentence_fields)
                if sentence._name in background:
                    print('.', end='', file=sys.stderr)
                    bg_count += 1
                else:
                    yield sentence
                    print('+', end='', file=sys.stderr)
                    fg_count += 1
                sys.stderr.flush()
    except KeyboardInterrupt:
        pass
    logger.info(f"Ignored  {bg_count}")
    logger.info(f"Captured {fg_count}")

def capture(target_file, sentence_source):
    """
    Write captured messages to the target file.
    
    :param target_file: an open file to which JSON text is written.
    :param sentence_source: an iterable source of sentences.
    """
    body = list(sentence_source)
    text = Encoder(indent=2, sort_keys=True).encode(body)
    target_file.write(text)
    target_file.write('\n')
    count = len(body)
    logger.info(f"Wrote {count} to {target_file.name}")
      
def get_options(argv):
    """
    Parses command-line options.
    
    :param argv: Command-line options from ``sys.argv[1:]``.
    :return: options namespace.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', '-o', action='store', default=None)
    parser.add_argument('input', action='store')
    parser.add_argument('--baud', action='store', type=int, default=4800)
    parser.add_argument('--timeout', action='store', type=int, default=10)
    return parser.parse_args(argv)
    
def main():
    """
    Main process for conversion: parse options, gather data until ``^C``,
    then writes the output file with the captured sentences.
    """
    options = get_options(sys.argv[1:])
    if options.output is None:
        capture(sys.stdout, sentence_iter(options))
    else:
        output_path = Path(options.output)
        if output_path.exists():
            logger.error(f"{output_path} already exists.")
            sys.exit(1)
        with open(options.output, 'w') as output_file:
            capture(output_file, sentence_iter(options))

if __name__ == "__main__":
    with Logging(stream=sys.stderr, level=logging.INFO):
        main()
