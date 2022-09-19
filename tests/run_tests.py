# =================================================================
#
# Terms and Conditions of Use
#
# Unless otherwise noted, computer program source code of this
# distribution is covered under Crown Copyright, Government of
# Canada, and is distributed under the MIT License.
#
# The Canada wordmark and related graphics associated with this
# distribution are protected under trademark law and copyright law.
# No permission is granted to use them outside the parameters of
# the Government of Canada's corporate identity program. For
# more information, see
# http://www.tbs-sct.gc.ca/fip-pcim/index-eng.asp
#
# Copyright title to all 3rd party software distributed with this
# software is held by the respective copyright holders as noted in
# those files. Users are asked to read the 3rd Party Licenses
# referenced with those assets.
#
# Copyright (c) 2021 Government of Canada
# Copyright (c) 2020, IBL Software Engineering spol. s r. o.
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# =================================================================

import os
import unittest

from lxml import etree
from pywcmp.ats import TestSuiteError, WMOCoreMetadataProfileTestSuite13
from pywcmp.kpi import (calculate_grade, group_kpi_results,
                        WMOCoreMetadataProfileKeyPerformanceIndicators)
from pywcmp.topics import TopicHierarchy
from pywcmp.util import parse_wcmp


def get_test_file_path(filename):
    """helper function to open test file safely"""

    if os.path.isfile(filename):
        return filename
    else:
        return f'tests/{filename}'


class WCMPATSTest(unittest.TestCase):
    """WCMP ATS tests of tests"""

    def setUp(self):
        """setup test fixtures, etc."""
        pass

    def tearDown(self):
        """return to pristine state"""
        pass

    def test_jma_raise(self):
        """Simple JMA Tests"""
        exml = etree.parse(get_test_file_path('data/md-WTPQ50RJTD-gmd.xml'))
        ts = WMOCoreMetadataProfileTestSuite13(exml)
        with self.assertRaises(TestSuiteError):
            ts.run_tests()

    def test_jma_inspect_errors(self):
        """Simple JMA Tests"""
        exml = etree.parse(get_test_file_path('data/md-SMJP01RJTD-gmd.xml'))
        ts = WMOCoreMetadataProfileTestSuite13(exml)
        try:
            ts.run_tests()
        except TestSuiteError as err:
            self.assertEqual(3, len(err.errors))


class WCMPKPITest(unittest.TestCase):
    """WCMP KPI tests of tests"""

    def setUp(self):
        """setup test fixtures, etc."""
        pass

    def tearDown(self):
        """return to pristine state"""
        pass

    def test_kpi_evaluate(self):
        exml = etree.parse(get_test_file_path('data/urn:x-wmo:md:int.wmo.wis::ca.gc.ec.msc-1.1.5.6.xml'))  # noqa

        kpis = WMOCoreMetadataProfileKeyPerformanceIndicators(exml)

        results = kpis.evaluate()

        self.assertEqual(results['summary']['total'], 60)
        self.assertEqual(results['summary']['score'], 41)
        self.assertEqual(results['summary']['percentage'], 68.333)
        self.assertEqual(results['summary']['grade'], "B")

    def test_calculate_grade(self):
        self.assertEqual(calculate_grade(98), 'A')
        self.assertEqual(calculate_grade(77), 'B')
        self.assertEqual(calculate_grade(66), 'B')
        self.assertEqual(calculate_grade(52), 'C')
        self.assertEqual(calculate_grade(41), 'D')
        self.assertEqual(calculate_grade(33), 'E')
        self.assertIsNone(calculate_grade(None))

        with self.assertRaises(ValueError):
            calculate_grade(101)

    def test_group_kpi_results(self):
        exml = etree.parse(get_test_file_path('data/urn:x-wmo:md:int.wmo.wis::ca.gc.ec.msc-1.1.5.6.xml'))  # noqa

        kpis = WMOCoreMetadataProfileKeyPerformanceIndicators(exml)

        results = kpis.evaluate()
        grouped_results = group_kpi_results(results)

        self.assertEqual(len(grouped_results), 5)

        expected_keys = [
            'content_information',
            'distribution_information',
            'enhancements',
            'mandatory',
            'summary'
        ]
        self.assertEqual(sorted(grouped_results.keys()), expected_keys)

        mandatory_kpis = ['kpi_001']
        self.assertEqual(sorted(grouped_results['mandatory'].keys()),
                         mandatory_kpis)

        content_information_kpis = [
            'kpi_002',
            'kpi_003',
            'kpi_004',
            'kpi_005',
            'kpi_006',
            'kpi_007',
            'summary'
        ]
        self.assertEqual(sorted(grouped_results['content_information'].keys()),
                         content_information_kpis)

        distribution_information_kpis = [
            'kpi_009',
            'kpi_010',
            'summary'
        ]
        self.assertEqual(sorted(
                         grouped_results['distribution_information'].keys()),
                         distribution_information_kpis)

        enhancements_kpis = [
            'kpi_008',
            'kpi_011',
            'summary'
        ]
        self.assertEqual(sorted(grouped_results['enhancements'].keys()),
                         enhancements_kpis)


class WCMPTopicHierarchyTest(unittest.TestCase):
    """WCMP Topic Hierarchy tests"""

    def setUp(self):
        """setup test fixtures, etc."""
        self.th = TopicHierarchy()
        pass

    def tearDown(self):
        """return to pristine state"""
        pass

    def test_validate(self):
        value = None
        with self.assertRaises(ValueError):
            _ = self.th.validate(value)

        value = 'invalid.topic.hierarchy'
        self.assertFalse(self.th.validate(value))

        value = 'wis2.a.cache'
        self.assertTrue(self.th.validate(value))

    def test_list_children(self):
        value = None
        expected_children = [
            'root',
            'version',
            'distribution',
            'country',
            'centre-id',
            'resource-type',
            'data-policy',
            'earth-system-domain'
        ]
        level, children = self.th.list_children(value)
        self.assertEqual(level, '/')
        self.assertEqual(children, expected_children)

        value = 'invalid.topic.hierarchy'
        with self.assertRaises(ValueError):
            level, children = self.th.list_children(value)

        value = 'wis2.a'
        expected_children = [
            'cache',
            'origin'
        ]
        level, children = self.th.list_children(value)
        self.assertEqual(level, 'distribution')
        self.assertEqual(children, expected_children)


class WCMPUtilTest(unittest.TestCase):
    """WCMP utility tests"""

    def setUp(self):
        """setup test fixtures, etc."""
        pass

    def tearDown(self):
        """return to pristine state"""
        pass

    def test_parse_wcmp(self):
        """test invalid input"""

        exml = parse_wcmp(get_test_file_path('data/urn:x-wmo:md:int.wmo.wis::ca.gc.ec.msc-1.1.5.6.xml'))  # noqa

        with self.assertRaises(RuntimeError):
            _ = parse_wcmp(get_test_file_path('data/not-wcmp.xml'))

        with self.assertRaises(RuntimeError):
            _ = parse_wcmp(get_test_file_path('data/not-xml.csv'))


if __name__ == '__main__':
    unittest.main()
