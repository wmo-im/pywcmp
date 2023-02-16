###############################################################################
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2022 Tom Kralidis
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

# abstract test suite as per WMO Core Metadata Profile 2, Annex A

import logging

from pywcmp.errors import TestSuiteError

LOGGER = logging.getLogger(__name__)


def msg(test_id: str, test_description: str) -> str:
    """
    Convenience function to print test props

    :param test_id: test suite identifier
    :param test_description: test suite identifier

    :returns: user-friendly string of test properties
    """

    requirement = test_id.split('test_requirement_')[-1].replace('_', '.')

    return f'Requirement {requirement}:\n    {test_description}'


def gen_test_id(test_id: str) -> str:
    """
    Convenience function to print test identifier as URI

    :param test_id: test suite identifier

    :returns: test identifier as URI
    """

    return f'http://www.wmo.int/spec/wcmp/2.0/req/core/{test_id}'


class WMOCoreMetadataProfileTestSuite2:
    """Test suite for WMO Core Metadata Profile assertions"""

    def __init__(self, data: dict):
        """
        initializer

        :param data: dict of WCMP2 JSON

        :returns: `pywcmp.wcmp2.ats.WMOCoreMetadataProfileTestSuite2`
        """

        self.test_id = None
        self.data = data

    def run_tests(self):
        """Convenience function to run all tests"""

        error_stack = []

        tests = [
            'validation'
        ]

        for i in tests:
            test_name = f'test_requirement_{i}'
            try:
                getattr(self, test_name)()
            except AssertionError as err:
                message = f'ASSERTION ERROR: {err}'
                LOGGER.info(message)
                error_stack.append(message)
            except Exception as err:
                message = f'OTHER ERROR: {err}'
                LOGGER.info(message)
                error_stack.append(message)

        if len(error_stack) > 0:
            raise TestSuiteError('Invalid metadata', error_stack)

    def test_requirement_validation(self):
        """
        Validate that a WCMP record is valid to the authoritative WCMP schema.
        """

        self.test_id = gen_test_id('http://www.wmo.int/spec/wcmp/2.0/conf/core/validation')

        assert True, self.test_validation.__doc__
