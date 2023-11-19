###############################################################################
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#          Ján Osuský <jan.osusky@iblsoft.com>
#
# Copyright (c) 2023 Tom Kralidis
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

import json
import os
import unittest

from pywcmp.ets import WMOCoreMetadataProfileTestSuite2
from pywcmp.wcmp2.kpi import (
    calculate_grade, WMOCoreMetadataProfileKeyPerformanceIndicators)
from pywcmp.wcmp2.topics import TopicHierarchy
from pywcmp.util import parse_wcmp


def get_test_file_path(filename):
    """helper function to open test file safely"""

    if os.path.isfile(filename):
        return filename
    else:
        return f'tests/{filename}'


class WCMP2ETSTest(unittest.TestCase):
    """WCMP2 ETS tests of tests"""

    def setUp(self):
        """setup test fixtures, etc."""
        pass

    def tearDown(self):
        """return to pristine state"""
        pass

    def test_pass(self):
        """Simple tests for a passing record"""
        with open(get_test_file_path('data/wcmp2-passing.json')) as fh:
            ts = WMOCoreMetadataProfileTestSuite2(json.load(fh))
            results = ts.run_tests()

            codes = [r['code'] for r in results['ets-report']['tests']]

            self.assertEqual(codes.count('FAILED'), 0)
            self.assertEqual(codes.count('PASSED'), 12)
            self.assertEqual(codes.count('SKIPPED'), 0)

    def test_fail(self):
        """Simple tests for a failing record"""
        with open(get_test_file_path('data/wcmp2-failing.json')) as fh:
            record = json.load(fh)
            ts = WMOCoreMetadataProfileTestSuite2(record)
            results = ts.run_tests()

            codes = [r['code'] for r in results['ets-report']['tests']]

            self.assertEqual(codes.count('FAILED'), 4)
            self.assertEqual(codes.count('PASSED'), 8)
            self.assertEqual(codes.count('SKIPPED'), 0)

            with self.assertRaises(ValueError):
                ts.run_tests(fail_on_schema_validation=True)


class WCMP2KPITest(unittest.TestCase):
    """WCMP KPI tests of tests"""

    def setUp(self):
        """setup test fixtures, etc."""
        pass

    def tearDown(self):
        """return to pristine state"""
        pass

    def test_kpi_evaluate(self):
        file_ = 'data/wcmp2-passing.json'
        with open(get_test_file_path(file_)) as fh:
            data = json.load(fh)

        kpis = WMOCoreMetadataProfileKeyPerformanceIndicators(data)

        results = kpis.evaluate()

        self.assertEqual(results['summary']['total'], 18)
        self.assertEqual(results['summary']['score'], 18)
        self.assertEqual(results['summary']['percentage'], 100)
        self.assertEqual(results['summary']['grade'], 'A')

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


class WIS2TopicHierarchyTest(unittest.TestCase):
    """WIS2 Topic Hierarchy tests"""

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

        value = 'invalid/topic/hierarchy'
        self.assertFalse(self.th.validate(value))

        value = 'cache/a/wis2'
        self.assertTrue(self.th.validate(value))

        value = 'a/wis2'
        self.assertFalse(self.th.validate(value))

        value = 'a/wis2'
        self.assertTrue(self.th.validate(value, fuzzy=True))

    def test_list_children(self):
        value = None
        children = self.th.list_children(value)
        self.assertEqual(sorted(children), ['cache', 'origin'])

        value = 'invalid.topic.hierarchy'
        with self.assertRaises(ValueError):
            _ = self.th.list_children(value)

        value = 'cache/c'
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

        with self.assertRaises(RuntimeError):
            _ = parse_wcmp(get_test_file_path('data/not-json.csv'))


if __name__ == '__main__':
    unittest.main()
