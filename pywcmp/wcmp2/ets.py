###############################################################################
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2023 Tom Kralidis
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

# executable test suite as per WMO Core Metadata Profile 2, Annex A

import json
import logging

from jsonschema.validators import Draft202012Validator

from pywcmp.bundle import WCMP2_FILES
from pywcmp.wcmp2.topics import TopicHierarchy

LOGGER = logging.getLogger(__name__)


def gen_test_id(test_id: str) -> str:
    """
    Convenience function to print test identifier as URI

    :param test_id: test suite identifier

    :returns: test identifier as URI
    """

    return f'http://www.wmo.int/spec/wcmp/2.0/req/conf/core/{test_id}'


class WMOCoreMetadataProfileTestSuite2:
    """Test suite for WMO Core Metadata Profile assertions"""

    def __init__(self, data: dict):
        """
        initializer

        :param data: dict of WCMP2 JSON

        :returns: `pywcmp.wcmp2.ets.WMOCoreMetadataProfileTestSuite2`
        """

        self.test_id = None
        self.record = data
        self.report = []

    def run_tests(self, fail_on_schema_validation=False):
        """Convenience function to run all tests"""

        results = []
        tests = []

        for f in dir(WMOCoreMetadataProfileTestSuite2):
            if all([
                    callable(getattr(WMOCoreMetadataProfileTestSuite2, f)),
                    f.startswith('test_requirement'),
                    not f.endswith('validation')]):

                tests.append(f)

        validation_result = self.test_requirement_validation()
        if validation_result['code'] == 'FAILED':
            if fail_on_schema_validation:
                msg = 'Record fails WCMP2 validation. Stopping ETS'
                LOGGER.error(msg)
                raise ValueError(msg)

        for t in tests:
            results.append(getattr(self, t)())

        return {
            'ets-report': results
        }

    def test_requirement_validation(self):
        """
        Validate that a WCMP record is valid to the authoritative WCMP schema.
        """

        status = {
            'id': gen_test_id('validation'),
            'code': 'PASSED'
        }

        schema = WCMP2_FILES / 'wcmp2-bundled.json'

        if not schema.exists():
            msg = "WCMP2 schema missing. Run 'pywcmp bundle sync' to cache"
            LOGGER.error(msg)
            raise RuntimeError(msg)

        LOGGER.debug(f'Validating {self.record} against {schema}')
        with schema.open() as fh:
            try:
                Draft202012Validator(json.load(fh)).validate(self.record)
            except Exception as err:
                status['code'] = 'FAILED'
                status['message'] = f'Invalid document: {repr(err)}'

        return status

    def test_requirement_identifier(self):
        """
        Validate that a WCMP record has a valid identifier.
        """

        status = {
            'id': gen_test_id('identifier'),
            'code': 'PASSED'
        }

        identifier = self.record['id']

        if identifier.count(':') != 5:
            status['code'] = 'FAILED'
            status['message'] = "identifier does not have six ':' delimiters"
            return status

        if not identifier.startswith('urn:x-wmo:md:'):
            status['code'] = 'FAILED'
            status['message'] = 'bad prefix'
            return status

        th = TopicHierarchy()

        country, centre_id = identifier.split(':')[3:5]

        if country not in th.list_children('origin/a/wis2'):
            status['code'] = 'FAILED'
            status['message'] = f'Invalid country: {country}'
            return status

        centre_ids = th.list_children(f'origin/a/wis2/{country}')
        if centre_id not in centre_ids:
            status['code'] = 'FAILED'
            status['message'] = f'Invalid centre_id: {centre_id}'
            return status

        if not identifier.isascii():
            status['code'] = 'FAILED'
            status['message'] = 'Bad characters in id'
            return status

        return status

    def test_requirement_conformance(self):
        """
        Validate that a WCMP record provides valid conformance information.
        """

        conformance_class = 'http://wis.wmo.int/spec/wcmp/2.0'

        status = {
            'id': gen_test_id('conformance'),
            'code': 'PASSED'
        }

        conformance = self.record.get('conformsTo')

        if conformance_class not in conformance:
            status['code'] = 'FAILED'
            status['message'] = f'Missing conformance class {conformance_class}'  # noqa

        return status

    def test_requirement_type(self):
        """
        Check for the existence of a valid properties.type property in
        the WCMP record.
        """

        status = {
            'id': gen_test_id('type'),
            'code': 'SKIPPED',
            'message': 'Test needs WCMP2 codelists'
        }

        # TODO: assess value against a codelist

        return status

    def test_requirement_extent_geospatial(self):
        """
        Check for the existence of a valid properties.type property in
        the WCMP record.
        """

        status = {
            'id': gen_test_id('extent_geospatial'),
            'code': 'PASSED',
            'message': 'Passes given schema is compliant/valid'
        }

        return status

    def test_requirement_extent_temporal(self):
        """
        Validate that a WCMP record provides a valid temporal extent property.
        """

        status = {
            'id': gen_test_id('extent_temporal'),
            'code': 'PASSED',
            'message': 'Passes given schema is compliant/valid'
        }

        return status

    def test_requirement_title(self):
        """
        Validate that a WCMP record provides a title property.
        """

        status = {
            'id': gen_test_id('title'),
            'code': 'PASSED',
            'message': 'Passes given schema is compliant/valid'
        }

        return status

    def test_requirement_description(self):
        """
        Validate that a WCMP record provides a description property.
        """

        status = {
            'id': gen_test_id('description'),
            'code': 'PASSED',
            'message': 'Passes given schema is compliant/valid'
        }

        return status

    def test_requirement_topic_hierarchy(self):
        """
        Validate that a WCMP record provides a valid WIS2 Topic Hierarchy.
        """

        status = {
            'id': gen_test_id('topic_hierarchy'),
            'code': 'PASSED'
        }

        topic_infra = str()
        topic = self.record['properties']['wmo:topicHierarchy']

        th = TopicHierarchy()

        if not th.validate(topic):
            status['code'] = 'FAILED'
            status['message'] = f'Invalid topic {topic}'
            return status

        try:
            channel, version, system, _ = topic.split('/', 3)
        except ValueError:
            status['code'] = 'FAILED'
            status['message'] = f'Topic {topic} does not have enough components'  # noqa
            return status

        for i in [channel, version, system]:
            topic_infra += i + '/'
            if th.validate(topic_infra):
                status['code'] = 'FAILED'
                status['message'] = f'Topic {topic} should not include levels 1-3'  # noqa

        return status

    def test_requirement_providers(self):
        """
        Validate that a WCMP record provides contact information for the
        metadata point of contact and originator of the data.
        """

        status = {
            'id': gen_test_id('providers'),
            'code': 'PASSED'
        }

        providers = self.record['properties']['providers']

        for role_type in ['originator', 'pointOfContact']:
            for p in providers:
                roles = [r['name'] for r in p['roles']]
                if not roles:
                    status['code'] = 'FAILED'
                    status['message'] = f'Missing role {role_type}'

        return status

    def test_requirement_creation_date(self):
        """
        Validate that a WCMP record provides a record creation date.
        """

        status = {
            'id': gen_test_id('record_creation_date'),
            'code': 'PASSED',
            'message': 'Passes given schema is compliant/valid'
        }

        return status

    def test_requirement_data_policy(self):
        """
        Validate that a WCMP record provides information about data policy and,
        if applicable additional information about licensing and/or rights.
        """

        name_found = False

        status = {
            'id': gen_test_id('data_policy'),
            'code': 'PASSED'
        }

        data_policy = self.record['properties']['wmo:dataPolicy']['name']

        if data_policy not in ['core', 'recommended']:
            status['code'] = 'FAILED'
            status['message'] = f'Invalid data policy {data_policy}'
            return status

        if data_policy == 'recommended':
            if 'additionalConditions' not in data_policy:
                status['code'] = 'FAILED'
                status['message'] = 'missing additionalConditions'
                return status

            for ac in data_policy['additionalConditions']:
                if 'name' in ac:
                    name_found = True

            if not name_found:
                status['code'] = 'FAILED'
                status['message'] = 'missing additionalConditions name'
                return status

            for ac in data_policy['additionalConditions']:
                if 'name' not in ac and 'scheme' not in ac:
                    status['code'] = 'FAILED'
                    status['message'] = 'missing additionalConditions name/scheme'  # noqa

        return status

    def test_requirement_links(self):
        """
        Validate that a WCMP record provides a link property.
        """

        canonical_found = False

        status = {
            'id': gen_test_id('links'),
            'code': 'PASSED'
        }

        links = self.record['links']

        for link in links:
            if link['rel'] == 'canonical':
                canonical_found = True

        if canonical_found:
            status['code'] = 'FAILED'
            status['message'] = 'missing at least one canonical link'

        return status
