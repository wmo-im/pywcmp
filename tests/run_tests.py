###############################################################################
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#          Ján Osuský <jan.osusky@iblsoft.com>
#
# Copyright (c) 2022 Tom Kralidis
# Copyright (c) 2022 Government of Canada
# Copyright (c) 2020 IBL Software Engineering spol. s r. o.
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
###############################################################################

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

        value = 'cache.a.wis2'
        self.assertTrue(self.th.validate(value))

    def test_list_children(self):
        value = None
        children = self.th.list_children(value)
        self.assertEqual(sorted(children), ['cache', 'origin'])

        value = 'invalid.topic.hierarchy'
        with self.assertRaises(ValueError):
            _ = self.th.list_children(value)

        value = 'cache.c'
        with self.assertRaises(ValueError):
            _ = self.th.list_children(value)

        value = 'cache'
        children = self.th.list_children(value)
        self.assertEqual(children, ['a'])


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
