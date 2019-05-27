# -*- coding: utf-8 -*-
# =================================================================
#
# Terms and Conditions of Use
#
# Unless otherwise noted, computer program source code of this
# distribution # is covered under Crown Copyright, Government of
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
# Copyright (c) 2017 Government of Canada
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

__version__ = '0.2.dev0'

# run test suite as per WMO Core Metadata Profile 1.3, Part 2

import sys
try:
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlopen
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
from lxml import etree
from wmo_cmp_ts import test_suite


def cli():
    """command line interface"""

    if len(sys.argv) < 2:
        print('Usage: %s <xmlfile or url>' % sys.argv[0])
        sys.exit(1)

    content = sys.argv[1]

    if content.startswith('http://'):  # URL
        content = StringIO(urlopen(content).read())

    EXML = etree.parse(content)

    ts = test_suite.WMOCoreMetadataProfileTestSuite13(EXML)

    ts.run_tests()
    # run the tests
    try:
        ts.run_tests()
        print('Successful!')
    except test_suite.TestSuiteError as err:
        print('\n'.join(err.message))
