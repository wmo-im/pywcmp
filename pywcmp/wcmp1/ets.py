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

# executable test suite as per WMO Core Metadata Profile 1.3, Part 2

import logging

from pywcmp.errors import TestSuiteError
from pywcmp.wcmp1.helpers import (get_codelists, get_string_or_anchor_value,
                                  NAMESPACES, nspath_eval, validate_iso_xml)

LOGGER = logging.getLogger(__name__)

CODELIST_PREFIX = 'http://wis.wmo.int/2012/codelists/WMOCodeLists.xml'


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

    return f'http://wis.wmo.int/2012/metadata/conf/{test_id}'


class WMOCoreMetadataProfileTestSuite13:
    """Test suite for WMO Core Metadata Profile assertions"""

    def __init__(self, exml):
        """
        initializer

        :param exml: `etree.ElementTree` object

        :returns: `pywcmp.wcmp1.ets.WMOCoreMetadataProfileTestSuite13`
        """

        self.test_id = None
        self.exml = exml  # serialized already
        self.namespaces = self.exml.getroot().nsmap

        # generate dict of codelists
        self.codelists = get_codelists()

    def run_tests(self):
        """Convenience function to run all tests"""

        tests = ['6_1_1', '6_1_2', '6_2_1', '6_3_1', '8_1_1',
                 '8_2_1', '8_2_2', '8_2_3', '8_2_4', '9_1_1',
                 '9_2_1', '9_3_1', '9_3_2']

        error_stack = []
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

    def test_requirement_6_1_1(self):
        """Requirement 6.1.1: Each WIS Discovery Metadata record shall validate without error against the XML schemas defined in ISO/TS 19139:2007."""
        self.test_id = gen_test_id('ISO-TS-19139-2007-xml-schema-validation')
        validate_iso_xml(self.exml)

    def test_requirement_6_1_2(self):
        """Requirement 6.1.2: Each WIS Discovery Metadata record shall validate without error against the rule-based constraints listed in ISO/TS 19139:2007 Annex A (Table A.1)."""
        self.test_id = gen_test_id('ISO-TS-19139-2007-rule-based-validation')
        # TODO

    def test_requirement_6_2_1(self):
        """Requirement 6.2.1: Each WIS Discovery Metadata record shall explicitly name all namespaces used within the record; use of default namespaces is prohibited."""
        self.test_id = gen_test_id('explicit-xml-namespace-identification')

        assert None not in self.namespaces, self.test_requirement_6_2_1.__doc__

    def test_requirement_6_3_1(self):
        """Requirement 6.3.1: Each WIS Discovery Metadata record shall declare the following XML namespace for GML: http://www.opengis.net/gml/3.2."""
        self.test_id = gen_test_id('gml-namespace-specification')

        if 'gml' in self.namespaces:
            assert self.namespaces['gml'] == NAMESPACES['gml'], self.test_requirement_6_3_1.__doc__

    def test_requirement_8_1_1(self):
        """Requirement 8.1.1: Each WIS Discovery Metadata record shall include one gmd:MD_Metadata/gmd:fileIdentifier attribute."""
        self.test_id = gen_test_id('fileIdentifier-cardinality')

        ids = self.exml.findall(nspath_eval('gmd:fileIdentifier'))
        assert len(ids) != 0, self.test_requirement_8_1_1.__doc__
        assert len(ids) < 2, self.test_requirement_8_1_1.__doc__ \
            + f' Multiple definitions found at lines {[id.sourceline for id in ids ]}.'

    def test_requirement_8_2_1(self):
        """Requirement 8.2.1: Each WIS Discovery Metadata record shall include at least one keyword from the WMO_CategoryCode code list."""
        self.test_id = gen_test_id('WMO_CategoryCode-keyword-cardinality')

        found = False

        # (i) check thesaurus
        wmo_cats = self._get_wmo_keyword_lists()
        assert len(wmo_cats) > 0, self.test_requirement_8_2_1.__doc__

        # (ii) check all WMO keyword sets valid codelist value
        line_numbers_with_error = []
        for cat in wmo_cats:
            keyword_values = self._get_keyword_values(cat.findall(nspath_eval('gmd:keyword')))
            for keyword_value in keyword_values:
                if keyword_value in self.codelists['wmo']['WMO_CategoryCode']:
                    found = True
                    break
            else:
                line_numbers_with_error.append(cat.sourceline)

        assert found, self.test_requirement_8_2_1.__doc__ \
            + f' Invalid keyword(s) found at line(s) {line_numbers_with_error}.'

    def test_requirement_8_2_2(self):
        """Requirement 8.2.2: Keywords from WMO_CategoryCode code list shall be defined as keyword type "theme"."""
        self.test_id = gen_test_id('WMO_CategoryCode-keyword-theme')

        wmo_cats = self._get_wmo_keyword_lists()
        assert len(wmo_cats) > 0, self.test_requirement_8_2_2.__doc__

        for cat in wmo_cats:
            for keyword_type in cat.findall(nspath_eval('gmd:type/gmd:MD_KeywordTypeCode')):
                assert keyword_type.text == 'theme', self.test_requirement_8_2_2.__doc__ \
                    + f' Invalid keyword found at line {keyword_type.sourceline}.'

    def test_requirement_8_2_3(self):
        """Requirement 8.2.3: All keywords sourced from a particular keyword thesaurus shall be grouped into a single instance of the MD_Keywords class."""
        self.test_id = gen_test_id('keyword-grouping')

        unique = 0
        thesauri = []
        wmo_cats = self._get_wmo_keyword_lists()
        assert len(wmo_cats) > 0, self.test_requirement_8_2_3.__doc__

        for cat in wmo_cats:
            for node in cat.findall(nspath_eval('gmd:thesaurusName/gmd:CI_Citation/gmd:title')):
                if node is not None:
                    node2 = node.find(nspath_eval('gmx:Anchor'))
                    if node2 is not None:  # search gmx:Anchor
                        value = node2.text
                    else:  # gmd:title should be WMO_CategoryCode
                        value = node.text
                    thesauri.append(value)

        if len(thesauri) == 1:
            unique = 1
        else:  # check if list if unique
            thesauri2 = list(set(thesauri))
            if len(thesauri) == len(thesauri2):
                unique = 1

        assert unique == 1, self.test_requirement_8_2_3.__doc__

    def test_requirement_8_2_4(self):
        """Requirement 8.2.4: Each WIS Discovery Metadata record describing geographic data shall include the description of at least one geographic bounding box defining the spatial extent of the data."""
        self.test_id = gen_test_id('geographic-bounding-box')

        hierarchy = self.exml.find(nspath_eval('gmd:hierarchyLevel/gmd:MD_ScopeCode'))
        assert hierarchy.text != 'nonGeographicDataset', self.test_requirement_8_2_4.__doc__ \
            + f' Dataset defined as non-geographic at line {hierarchy.sourceline}.'

        bbox = self.exml.find(nspath_eval('gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox'))
        assert bbox is not None, self.test_requirement_8_2_4.__doc__

    def test_requirement_9_1_1(self):
        """Requirement 9.1.1: A WIS Discovery Metadata record describing data for global exchange via the WIS shall indicate the scope of distribution using the keyword "GlobalExchange" of type "dataCenter" from thesaurus WMO_DistributionScopeCode."""
        self.test_id = gen_test_id('identification-of-globally-exchanged-data')

        LOGGER.debug('Checking if discovery metadata identifies data for global exchange')
        if not self._is_for_global_exchange():
            return

        dist_cats = self._get_wmo_keyword_lists('WMO_DistributionScopeCode')
        if len(dist_cats) > 0:
            for cat in dist_cats:
                for keyword_type in cat.findall(nspath_eval('gmd:type/gmd:MD_KeywordTypeCode')):
                    assert keyword_type.text == 'dataCentre', self.test_requirement_9_1_1.__doc__ \
                        + f' Invalid keyword found at line {keyword_type.sourceline}.'
                    keyword_values = self._get_keyword_values(cat.findall(nspath_eval('gmd:keyword')))
                    assert 'GlobalExchange' in keyword_values, self.test_requirement_9_1_1.__doc__ \
                        + f' Invalid keyword(s) ({keyword_values}) found at line {keyword_type.sourceline}.'

    def test_requirement_9_2_1(self):
        """Requirement 9.2.1: A WIS Discovery Metadata record describing data for global exchange via the WIS shall have a gmd:MD_Metadata/gmd:fileIdentifier attribute formatted as follows (where {uid} is a unique identifier derived from the GTS bulletin or file name): urn:x-wmo:md:int.wmo.wis::{uid}."""
        self.test_id = gen_test_id('fileIdentifier-for-globally-exchanged-data')

        LOGGER.debug('Checking if discovery metadata identifies data for global exchange')
        if not self._is_for_global_exchange():
            return

        mask = 'urn:x-wmo:md:int.wmo.wis::'
        identifier_element = self.exml.find(nspath_eval('gmd:fileIdentifier/gco:CharacterString'))
        identifier = identifier_element.text

        assert identifier.startswith(mask), self.test_requirement_9_2_1.__doc__ \
            + f' Invalid identifier ({identifier}) found at line {identifier_element.sourceline}.'

    def test_requirement_9_3_1(self):
        """Requirement 9.3.1: A WIS Discovery Metadata record describing data for global exchange via the WIS shall indicate the WMO Data License as Legal Constraint (type: "otherConstraints") using one and only one term from the WMO_DataLicenseCode code list."""
        self.test_id = gen_test_id('WMO-data-policy-for-globally-exchanged-data')

        LOGGER.debug('Checking if discovery metadata identifies data for global exchange')
        if not self._is_for_global_exchange():
            return

        count = 0

        xpath = 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:resourceConstraints/gmd:MD_LegalConstraints/gmd:otherConstraints'
        other_constraints_elements = self.exml.findall(nspath_eval(xpath))
        for constr_element in other_constraints_elements:
            constr_vals = get_string_or_anchor_value(constr_element)
            for constr in constr_vals:
                if constr in self.codelists['wmo']['WMO_DataLicenseCode']:
                    count += 1
        if len(other_constraints_elements) == 0:
            assert count == 1, self.test_requirement_9_3_1.__doc__
        else:
            assert count == 1, self.test_requirement_9_3_1.__doc__ \
                + f' Please check contraints at lines {[c.sourceline for c in other_constraints_elements ]}.'

    def test_requirement_9_3_2(self):
        """Requirement 9.3.2: A WIS Discovery Metadata record describing data for global exchange via the WIS shall indicate the GTS Priority as Legal Constraint (type: "otherConstraints") using one and only one term from the WMO_GTSProductCategoryCode code list."""
        self.test_id = gen_test_id('GTS-priority-for-globally-exchanged-data')

        LOGGER.debug('Checking if discovery metadata identifies data for global exchange')
        if not self._is_for_global_exchange():
            return

        count = 0
        xpath = 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:resourceConstraints/gmd:MD_LegalConstraints/gmd:otherConstraints'
        other_constraints_elements = self.exml.findall(nspath_eval(xpath))
        for constr_element in other_constraints_elements:
            constr_vals = get_string_or_anchor_value(constr_element)
            for constr in constr_vals:
                if constr in self.codelists['wmo']['WMO_GTSProductCategoryCode']:
                    count += 1
        if len(other_constraints_elements) == 0:
            assert count == 1, self.test_requirement_9_3_2.__doc__
        else:
            assert count == 1, self.test_requirement_9_3_2.__doc__ \
                + f' Please check contraints at lines {[c.sourceline for c in other_constraints_elements ]}.'

    def _get_wmo_keyword_lists(self, code: str = 'WMO_CategoryCode') -> list:
        """
        Helper function to retrieve all keyword sets by code

        :param code: code list name (default: `WMO_CategoryCode`)

        :returns: `list` of keyword set by code
        """

        wmo_cats = []

        keywords_sets = self.exml.findall(nspath_eval('gmd:identificationInfo/gmd:MD_DataIdentification/gmd:descriptiveKeywords/gmd:MD_Keywords'))

        for kwd in keywords_sets:  # find thesaurusname
            node = kwd.find(nspath_eval('gmd:thesaurusName/gmd:CI_Citation/gmd:title'))
            if node is not None:
                node2 = node.find(nspath_eval('gmx:Anchor'))
                if node2 is not None:  # search gmx:Anchor
                    value = node2.get(nspath_eval('xlink:href'))
                    if value == f'{CODELIST_PREFIX}#{code}':
                        wmo_cats.append(kwd)
                else:  # gmd:title should be code var
                    value = node.find(nspath_eval('gco:CharacterString'))
                    if value is not None and value.text == code:
                        wmo_cats.append(kwd)
        return wmo_cats

    def _get_keyword_values(self, keyword_nodes: list) -> list:
        values = []
        for keyword_node in keyword_nodes:
            anchor_node = keyword_node.find(nspath_eval('gmx:Anchor'))
            if anchor_node is not None:
                value = anchor_node.get(nspath_eval('xlink:href'))
                values.append(value)
            else:
                value_node = keyword_node.find(nspath_eval('gco:CharacterString'))
                if value_node is not None:
                    values.append(value_node.text)
        return values

    def _is_for_global_exchange(self) -> bool:
        keyword_nodes = self.exml.findall(nspath_eval('gmd:identificationInfo/gmd:MD_DataIdentification/gmd:descriptiveKeywords/gmd:MD_Keywords//gmd:keyword'))

        keyword_values = self._get_keyword_values(keyword_nodes)

        return 'GlobalExchange' in keyword_values
