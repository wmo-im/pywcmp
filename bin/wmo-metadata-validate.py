#!/usr/bin/env python

# run test suite as per WMO Core Metadata Profile 1.3, Part 2

import sys
from lxml import etree
from wmo_cmp_ts import test_suite

if len(sys.argv) < 2:
    print 'Usage: %s <xmlfile>' % sys.argv[0]
    sys.exit(1)

EXML = etree.parse(sys.argv[1])

TS = test_suite.WMOCoreMetadataProfileTestSuite13(EXML)

# run the tests
try:
    TS.run_tests()
except ValueError, err:
    print err
