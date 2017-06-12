"""
Merge waypoints from two sources:

1.  The master GPX file. These have precedence.
    Any duplicates here create warnings.

2.  A new GPX file. Duplicates from here are dropped.

The output is a combined list with duplicated locations removed.
This becomes the new master.
"""
from nmeatools.waypoint_to_gpx import waypoints_to_gpx
from nmeatools.nmea_data_lazy import Sentence_Factory
from nmeatools.haversine import nm_haversine
from nmeatools.common import logged, Logging

from xml.etree import ElementTree
from pathlib import Path
import sys
import logging

@logged
class Waypoint:
    """Behaves a little bit like an NMEA GPWPL sentence."""
    def __init__(self, lat, lon, name, time, sym):
        self.latitude = float(lat)
        self.longitude = float(lon)
        self.name = name
        self.time = time
        self.sym = sym
        self._name = 'GPWPL'
    def __repr__(self):
        return f"{self.latitude} {self.longitude} {self.time} {self.sym} {self.name}"
    @property
    def args(self):
        lat_h = b'N' if self.latitude > 0 else b'S'
        lat_deg, lat_min = divmod(abs(self.latitude), 1)
        lat_nmea = '{:02d}{:02.4f}'.format(int(lat_deg), lat_min*60).encode('ascii')
        lon_h = b'E' if self.longitude > 0 else b'W'
        lon_deg, lon_min = divmod(abs(self.longitude), 1)
        lon_nmea = '{:03d}{:02.4f}'.format(int(lon_deg), lon_min*60).encode('ascii')
        return b'GPWPL', lat_nmea, lat_h, lon_nmea, lon_h, self.name.encode('ascii')
    def distance(self, other):
        """Distance in NM."""
        return nm_haversine(self.latitude, self.longitude, other.latitude, other.longitude)

        
gpx_namespace = {'gpx': 'http://www.topografix.com/GPX/1/1'}

def waypoint_iter(root, namespace):
    for doc in root.findall('gpx:wpt', namespace):
        latitude = doc.attrib['lat']
        longitude = doc.attrib['lon']
        name_element = doc.find('gpx:name', namespace)
        name = name_element.text if name_element is not None else None
        time_element = doc.find('gpx:time', namespace)
        time = time_element.text if time_element is not None else None
        sym_element = doc.find('gpx:sym', namespace)
        sym = sym_element.text if sym_element is not None else None
        yield Waypoint(latitude, longitude, name, time, sym)
        
logger = logging.getLogger("merge")

def merge(master_path=Path("/Volumes/NO NAME/WaypointsRoutesTracks.gpx"), 
    update_path = Path('/Users/slott/Documents/Sailing/Cruise History/routes/waypoints.gpx')
    ):
    GPS_ERROR = 32/6060  # 32′ GPS Error Circle
    
    master_tree = ElementTree.parse(str(master_path))
    master_root = master_tree.getroot()

    logger.info(f"MASTER from {master_path}")
    base = list(waypoint_iter(master_root, gpx_namespace))
    for i in range(len(base)):
        for j in range(i):
            d = base[i].distance(base[j]) 
            if d <= GPS_ERROR:
                logger.info(f"{base[i].name} possible duplicate {d:.4f} {base[j].name}")

    update_tree = ElementTree.parse(str(update_path))
    update_root = update_tree.getroot()

    logger.info(f"UPDATE from {update_path}")
    unique_waypoints = []
    for wpt in waypoint_iter(update_root, gpx_namespace):
        closest = min((wpt.distance(b_wpt), b_wpt) for b_wpt in base)
        d, close_wpt = closest
        if d <= GPS_ERROR:
            logger.info(f"{wpt.name} near {d:.4f} {close_wpt.name}")
        else:
            unique_waypoints.append(wpt)

    # Emit GPX file.
    document = waypoints_to_gpx(unique_waypoints, 'merged_waypoints.gpx', "2017 Merged Red Ranger Waypoints.")
    print(document.toprettyxml(indent="  "))
    
if __name__ == "__main__":
    with Logging(stream=sys.stderr, level=logging.INFO):
        merge()
