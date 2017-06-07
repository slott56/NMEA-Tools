#!/usr/bin/env python3
"""
Convert waypoints or routes to GPX format for iNavX/GPSNavX

Synopsis
========

..  program:: waypoint_to_gpx

::

    usage: waypoint_to_gpx.py [-h] --desc DESC [--force]
                              [--format {.gpx,.csv,.kml}]
                              [input [input ...]]

Arguments
=========

..  option:: input

    One or more files to convert. These must be JSON-format files
    created by the :program:`nmea_capture` program.

Options
=======

optional arguments:

..  option:: -h, --help
    
    show this help message and exit

..  option:: --desc DESC, -d DESC

    Description

..  option:: --force

    Force overwrite of the .gpx output file.

..  option:: --format {.gpx,.csv,.kml}, -f {.gpx,.csv,.kml}

    The output formaat. Currently, only .gpx is supported and it's the default.
"""
from nmeatools.nmea_data import Decoder
from nmeatools.common import logged, Logging

from xml.dom import getDOMImplementation
import xml.etree.ElementTree as xml
from pathlib import Path
import argparse
import sys
import logging

logger = logging.getLogger(__name__)

def build_gpx(document, name, description):
    """Create the ``<gpx>`` Element, inserting metadata.
    
    :param document: The root document
    :param name: The string name to put in the metadata
    :param description: the string description to put in the metadata
    :returns: the ``<gpx>`` element
    """
    gpx = document.createElement("gpx")
    gpx.setAttribute("version", "1.1")
    gpx.setAttribute("creator", "NMEA-Tools-1.1")
    metadata = document.createElement("metadata")
    name_node = document.createElement("name")
    name_node.appendChild(document.createTextNode(name))
    metadata.appendChild(name_node)
    desc_node = document.createElement("desc")
    desc_node.appendChild(document.createTextNode(description))
    metadata.appendChild(desc_node)
    gpx.appendChild(metadata)
    document.appendChild(gpx)
    return gpx

def build_waypoint_location(document, s):
    """Create a ``<wpt>`` element, inserting a ``<name>`` element.
    
    :param document: The root document
    :param s: An :class:`nmeatools.nmea_data.GPWPL` instance.
    :returns: the ``<wpt>`` e,ement
    """
    assert s._name == 'GPWPL', f"Unexpected NMEA capture document {s}"
    wpt = document.createElement("wpt")
    wpt.setAttribute("lat", str(s.lat))
    wpt.setAttribute("lon", str(s.lon))
    name = document.createElement("name")
    name.appendChild(document.createTextNode(s.name))
    wpt.appendChild(name)
    return wpt

def build_routepoint(document, s, sym=None):
    """Create a ``<rtept>`` element, inserting a ``<name>`` element (optionally a ``<sym>``).

    :param document: The root document
    :param s: An :class:`nmeatools.nmea_data.GPWPL` instance.
    :param sym: An optional string with a symbol name to include.
    :returns: the ``<rtept>`` e,ement    
    """
    assert s._name == 'GPWPL', f"Unexpected NMEA capture document {s}"
    wpt = document.createElement("rtept")
    wpt.setAttribute("lat", str(s.lat))
    wpt.setAttribute("lon", str(s.lon))
    name = document.createElement("name")
    name.appendChild(document.createTextNode(s.name))
    wpt.appendChild(name)
    if sym:
        sym_tag = document.createElement("sym")
        sym_tag.appendChild(document.createTextNode(sym))
        wpt.appendChild(sym_tag)
    return wpt

def waypoints_to_gpx(sentences, name, description):
    """
    Create GPX doc with waypoints.
    
    :param sentences: iterable sequence of :class:`nmeatools.nmea_data.GPWPL` instances
    :param name: The string name to put in the metadata
    :param description: the string description to put in the metadata
    :returns: ``<gpx>`` element containing the ``<wpt>`` waypoints.
    """
    impl = getDOMImplementation()
    document = impl.createDocument(None, None, None)
    gpx = build_gpx(document, name, description)
    
    for s in sentences:
        logger.info(f"{s}")
        wpt = build_waypoint_location(document, s)        
        gpx.appendChild(wpt)

    return document

def route_to_gpx(sentences, name, description):
    """
    Create GPX doc with a route that contains waypoints.
    
    1.  Save waypoint as {name : sentence} map.
    2.  Flatten route sentences into a single list of waypoints.
        This presumes the :class:`nmeatools.nmea_data.GPRTE` sentences
        are already in their proper order.
    
    :param sentences: iterable sequence of :class:`nmeatools.nmea_data.GPWPL` and
        :class:`nmeatools.nmea_data.GPRTE` instances
    :param name: The string name to put in the metadata
    :param description: the string description to put in the metadata
    :returns: ``<gpx>`` element containing the ``<rte>`` and ``<rtpte>`` waypoints.
    
    """
    names = set()
    waypoints = {}
    route_points = []
    for s in sentences:
        logger.info(f"{s}")
        if s._name == 'GPWPL':
            waypoints[s.name] = s
        elif s._name == 'GPRTE':
            route_points.extend(s.waypoints)
            names.add(s.id)
        else:
            assert s._name not in ('GPWPL', 'GPRTE'), f"Unexpected NMEA capture document {s}"
        
    impl = getDOMImplementation()
    document = impl.createDocument(None, None, None)
    gpx = build_gpx(document, name, description)
    
    rte = document.createElement('rte')
    name_node = document.createElement("name")
    name_node.appendChild(document.createTextNode(", ".join(names)))
    rte.appendChild(name_node)
    desc_node = document.createElement("desc")
    desc_node.appendChild(document.createTextNode(""))
    rte.appendChild(desc_node)
    gpx.appendChild(rte)

    for rp in route_points:
        s = waypoints[rp]
        wpt = build_routepoint(document, s)        
        rte.appendChild(wpt)

    return document
    
def convert_waypoints(waypoints_path, description="2017 Waypoints from Red Ranger chartplotter."):
    """
    Load JSON document with GPWPL sentences; return GPX representation.
    
    :param waypoints_path: Path with location of waypoints in JSON notation.
    :param description: Description to insert into the metadata.
    :returns: root document with ``<gpx>`` and ``<wpt>`` tags.
    """
    logger.info(f"Read waypoints from {waypoints_path}")
    text = waypoints_path.read_text()
    sentence_list = Decoder().decode(text)
    document = waypoints_to_gpx(sentence_list, waypoints_path.name, description)
    items = len(sentence_list)
    logger.info(f"{items} sentences read")
    return document.toprettyxml(indent="  ")

def convert_route(route_path, description="2017 Waypoints from Red Ranger chartplotter."):
    """
    Load JSON document with GPWPL and GPRTE sentences; return GPX representation.
    
    :param route_path: Path with location of routes in JSON notation.
    :param description: Description to insert into the metadata.
    :returns: root document with ``<gpx>`` and ``<rte>`` and ``<rtept>`` tags.
    """
    logger.info(f"Read route from {route_path}")
    text = route_path.read_text()
    sentence_list = Decoder().decode(text)
    document = route_to_gpx(sentence_list, route_path.name, description)
    items = len(sentence_list)
    logger.info(f"{items} sentences read")
    return document.toprettyxml(indent="  ")

def get_options(argv):
    """
    Parses command-line options.
    
    :param argv: Command-line options from ``sys.argv[1:]``.
    :return: options namespace.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs='*')
    parser.add_argument("--desc", "-d", action='store', help="Description", required=True)
    parser.add_argument('--force', action='store_true', help="Force overwrite", default=False)
    parser.add_argument("--format", "-f", action='store', choices=('.gpx', '.csv', '.kml'), default='.gpx')
    options = parser.parse_args(argv)
    if options.format != '.gpx':
        raise ValueError("Only .gpx is supported currently.")
    return options

def main():
    """
    Main process for conversion: parse options, process files.  Only the GPX output
    is supported currently.
    
    Each file is scanned to see what it contains.
    
    -   'GPRTE', 'GPWPL' -- a route
    -   'GPWPL' -- only waypoints
    
    The output path matches the input path with a suffix changed to :file:`.gpx`.
    """
    result = 0  # All OK
    options = get_options(sys.argv[1:])
    for name in options.input:
        input_path = Path(name)
        output_path = input_path.with_suffix(options.format)
        if output_path.exists() and not options.force:
            logger.error("Output file already exists.")
            result = 1  # Something failed
            continue
        # Scan file for sentences.
        text = input_path.read_text()
        types = set(s._name for s in Decoder().decode(text))
        if {'GPRTE', 'GPWPL'} <= types:
            gpx = convert_route(input_path, options.desc)
        elif {'GPWPL'} <= types:
            gpx = convert_waypoints(input_path, options.desc)
        else:
            logger.error(f"Sorry, couldn't process file of {types} sentences.")
            result = 1  # Something failed
            continue
        logger.info(f"Writing {output_path}")
        with output_path.open('w') as target:
            target.write(gpx)
            target.write('\n')
    sys.exit(result)

if __name__ == "__main__":
    with Logging(stream=sys.stderr, level=logging.INFO):
        main()
