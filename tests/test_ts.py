# -*- coding: ISO-8859-15 -*-

import unittest
from lxml import etree
from wmo_cmp_ts import test_suite


class WmoTestSuiteTest(unittest.TestCase):
    """Test suite for package Foo"""
    def setUp(self):
        """setup test fixtures, etc."""
        pass

    def tearDown(self):
        """return to pristine state"""
        pass

    def test_jma_raise(self):
        """Simple JMA Tests"""
        exml = etree.parse('data/md-WTPQ50RJTD-gmd.xml')
        ts = test_suite.WMOCoreMetadataProfileTestSuite13(exml)
        with self.assertRaises(test_suite.TestSuiteError):
            ts.run_tests()

    def test_jma_inspect_errors(self):
        """Simple JMA Tests"""
        exml = etree.parse('data/md-SMJP01RJTD-gmd.xml')
        ts = test_suite.WMOCoreMetadataProfileTestSuite13(exml)
        try:
            ts.run_tests()
        except test_suite.TestSuiteError, err:
            print str(err)
            self.assertEquals(3, len(err.message))

if __name__ == '__main__':
    unittest.main()
