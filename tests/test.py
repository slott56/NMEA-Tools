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
import nmeatools.nmea_data
import nmeatools.waypoint_to_gpx

def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(nmeatools.nmea_capture))
    tests.addTests(doctest.DocTestSuite(nmeatools.nmea_data))
    tests.addTests(doctest.DocTestSuite(nmeatools.waypoint_to_gpx))
    return tests

if __name__ == "__main__":
    unittest.main()
