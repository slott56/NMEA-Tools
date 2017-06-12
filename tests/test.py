"""
Unit Test Cases.

MacBookPro-SLott:NMEA-Tools slott$ PYTHONPATH=. python3 tests/test.py
..........
----------------------------------------------------------------------
Ran 10 tests in 0.005s

OK

"""

import unittest
import doctest
import nmeatools.nmea_capture
import nmeatools.nmea_data_eager
import nmeatools.nmea_data_lazy
import nmeatools.nmea_device
import nmeatools.waypoint_merge
import nmeatools.waypoint_to_gpx

def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(nmeatools.nmea_capture))
    tests.addTests(doctest.DocTestSuite(nmeatools.nmea_data_eager))
    tests.addTests(doctest.DocTestSuite(nmeatools.nmea_data_lazy))
    tests.addTests(doctest.DocTestSuite(nmeatools.nmea_device))
    tests.addTests(doctest.DocTestSuite(nmeatools.waypoint_merge))
    tests.addTests(doctest.DocTestSuite(nmeatools.waypoint_to_gpx))
    return tests

if __name__ == "__main__":
    unittest.main()
