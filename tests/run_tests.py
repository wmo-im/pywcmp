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
# Copyright (c) 2019 Government of Canada
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
from wmo_cmp_ts import test_suite


def get_test_file_path(filename):
    """helper function to open test file safely"""

    if os.path.isfile(filename):
        return filename
    else:
        return 'tests/{}'.format(filename)


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
        exml = etree.parse(get_test_file_path('data/md-WTPQ50RJTD-gmd.xml'))
        ts = test_suite.WMOCoreMetadataProfileTestSuite13(exml)
        with self.assertRaises(test_suite.TestSuiteError):
            ts.run_tests()

    def test_jma_inspect_errors(self):
        """Simple JMA Tests"""
        exml = etree.parse(get_test_file_path('data/md-SMJP01RJTD-gmd.xml'))
        ts = test_suite.WMOCoreMetadataProfileTestSuite13(exml)
        try:
            ts.run_tests()
        except test_suite.TestSuiteError as err:
            self.assertEqual(3, len(err.errors))


if __name__ == '__main__':
    unittest.main()
