#!/usr/bin/env python

# run test suite as per WMO Core Metadata Profile 1.3, Part 2

import sys
from lxml import etree
from wmo_cmp_ts import test_suite

if len(sys.argv) < 2:
    print 'Usage: %s <xmlfile>' % sys.argv[0]
    sys.exit(1)

TESTS = ['6_1_1', '6_1_2', '6_2_1', '6_3_1', '8_1_1',
         '8_2_1', '8_2_2', '8_2_3', '8_2_4', '9_1_1',
         '9_2_1', '9_3_1', '9_3_2']

EXML = etree.parse(sys.argv[1])

TS = test_suite.WMOCoreMetadataProfileTestSuite13(EXML)

# run the tests

for i in TESTS:
    test_name = 'test_requirement_%s' % i
    print test_name
    try:
        getattr(TS, test_name)()
    except Exception, err:
        print err
