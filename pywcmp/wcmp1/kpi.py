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

# WMO Core Metadata Profile Key Performance Indicators (KPIs)

import os
import logging
import re

from bs4 import BeautifulSoup

from pywcmp.util import check_spelling, check_url
from pywcmp.wcmp1.ets import WMOCoreMetadataProfileTestSuite13
from pywcmp.errors import TestSuiteError
from pywcmp.wcmp1.helpers import (get_codelists, get_keyword_info,
                                  get_string_or_anchor_value,
                                  get_string_or_anchor_values, nspath_eval,
                                  parse_time_position)

LOGGER = logging.getLogger(__name__)

# round percentages to x decimal places
ROUND = 3

THISDIR = os.path.dirname(os.path.realpath(__file__))


class WMOCoreMetadataProfileKeyPerformanceIndicators:
    """Key Performance Indicators for WMO Core Metadata Profile"""

    def __init__(self, exml):
        """
        initializer

        :param exml: `etree.ElementTree` object

        :returns: `pywcmp.wcmp1.kpi.WMOCoreMetadataProfileKeyPerformanceIndicators`
        """

        self.exml = exml  # serialized already
        self.namespaces = self.exml.getroot().nsmap

        # remove empty (default) namespace to avoid exceptions in exml.xpath
        if None in self.namespaces:
            LOGGER.debug('Removing default (None) namespace. This XML is destined to fail.')
            none_namespace = self.namespaces[None]
            self.namespaces[none_namespace.split('/')[-1]] = none_namespace
            self.namespaces.pop(None)

        # add namespace that our Xpath searches depend on but that may not exist in certain documents
        if 'gmx' not in self.namespaces:
            self.namespaces['gmx'] = 'http://www.isotc211.org/2005/gmx'

        # generate dict of codelists
        self.codelists = get_codelists()

    @property
    def identifier(self):
        """
        Helper function to derive a metadata record identifier

        :returns: metadata record identifier
        """

        xpath = '//gmd:fileIdentifier/gco:CharacterString/text()'

        return self.exml.xpath(xpath, namespaces=self.namespaces)[0]

    def _get_link_lists(self) -> set:
        """
        Helper function to retrieve all link elements (gmx:Anchor, gmd:URL, ...)

        :returns: `set` containing strings (URLs)
        """

        links = []

        # add possibly missing namespace
        xpath_namespaces = self.namespaces
        if xpath_namespaces.get('gmx') is None:
            xpath_namespaces['gmx'] = 'http://www.isotc211.org/2005/gmx'
        if xpath_namespaces.get('xlink') is None:
            xpath_namespaces['xlink'] = 'http://www.w3.org/1999/xlink'

        xpaths = [
            '//gmd:URL/text()',
            '//gmx:Anchor/@xlink:href',
            '//gmd:CI_DateTypeCode/@codeList',
            '//gmd:graphicOverview/gmd:MD_BrowseGraphic/gmd:fileName/gco:CharacterString/text()'
        ]

        for xpath in xpaths:
            new_links = self.exml.xpath(xpath, namespaces=xpath_namespaces)
            LOGGER.debug(f'Found {len(new_links)} links with {xpath}')
            links += new_links

        return set(links)

    def kpi_001(self) -> tuple:
        """
        Implements KPI-1: WCMP 1.3, Part 2 Compliance

        :returns: `tuple` of KPI name, achieved score, total score, and comments
        """

        name = 'KPI-1: WCMP 1.3, Part 2 Compliance'

        LOGGER.info(f'Running {name}')
        LOGGER.debug('Running ETS tests')
        ts = WMOCoreMetadataProfileTestSuite13(self.exml)

        total = 13
        comments = []

        # run the tests
        score = total
        try:
            ts.run_tests()
        except TestSuiteError as err:
            allowed_errors = ['6.1.1', '6.1.2', '6.2.1']
            error_regex = re.compile(r'^ASSERTION ERROR: Requirement (\d\.\d.\d).*')
            for error in err.errors:
                failed_test = error_regex.match(error)
                if failed_test is None or failed_test.group(1) not in allowed_errors:
                    score -= 1
                else:
                    LOGGER.debug(f'Skipping failure of the requirement {failed_test.group(1)}')
                    err.errors.remove(error)
            score = total - len(err.errors)
            comments = err.errors

        return name, total, score, comments

    def kpi_002(self) -> tuple:
        """
        Implements KPI-2: Good quality title

        :returns: `tuple` of KPI name, achieved score, total score, and comments
        """

        total = 0
        score = 0
        comments = []

        name = 'KPI-2: Good quality title'

        LOGGER.info(f'Running {name}')

        xpath = '//gmd:identificationInfo//gmd:citation/gmd:CI_Citation/gmd:title/gco:CharacterString'

        LOGGER.debug(f'Testing all titles at {xpath}')

        titles = self.exml.xpath(xpath, namespaces=self.namespaces)

        total = 8
        if len(titles) > 0:
            t = titles[0]
            title = t.text
            LOGGER.debug('Title is present')
            score += 1
            title_words = []

            try:
                LOGGER.debug('Testing number of words')
                title_words = title.split()
            except Exception as err:
                LOGGER.debug(err)
                return

            title_words = title.split()

            LOGGER.debug('Testing number of words')
            if len(title_words) >= 3:
                score += 1
            else:
                comments.append(f'Line {t.sourceline}: title has less than 3 words')

            LOGGER.debug('Testing number of characters')
            if len(title) <= 150:
                score += 1
            else:
                comments.append(f'Line {t.sourceline}: title has more than 150 characters')

            LOGGER.debug('Testing for alphanumeric characters')
            if all(x.isalnum() for x in title_words):
                score += 1
            else:
                comments.append(f'Line {t.sourceline}: title contains non-printable characters')

            LOGGER.debug('Testing for title case')
            if title.istitle():
                score += 1
            else:
                comments.append(f'Line {t.sourceline}: title is not title case')

            LOGGER.debug('Testing for acronyms')
            if len(re.findall(r'([A-Z]\.*){2,}s?', title)) <= 3:
                score += 1
            else:
                comments.append(f'Line {t.sourceline}: title has more than 3 acronyms')

            LOGGER.debug('Testing for bulletin headers')
            has_bulletin_header = re.search(r'[A-Z]{4}\d{2}[\s_]*[A-Z]{4}', title)
            if not has_bulletin_header:
                score += 1
            else:
                score -= 1
                comments.append(f'Line {t.sourceline}: title contains bulletin header')

            LOGGER.debug('Testing for spelling')
            misspelled = check_spelling(title)

            if not misspelled:
                score += 1
            else:
                comments.append(f'Line {t.sourceline}: title contains spelling errors {misspelled}')

        return name, total, score, comments

    def kpi_003(self) -> tuple:
        """
        Implements KPI-3: Good quality abstract

        :returns: `tuple` of KPI name, achieved score, total score, and comments
        """

        total = 0
        score = 0
        comments = []

        name = 'KPI-3: Good quality abstract'

        LOGGER.info(f'Running {name}')

        xpath = '//gmd:identificationInfo//gmd:abstract/gco:CharacterString'

        LOGGER.debug(f'Testing all abstracts at {xpath}')

        abstracts = self.exml.xpath(xpath, namespaces=self.namespaces)

        for a in abstracts:
            abstract = a.text
            LOGGER.debug('Abstract is present')
            total += 4

            if abstract is None:
                comments.append(f'Abstract at line {a.sourceline}: is null')
                continue

            LOGGER.debug('Testing number of characters')
            if 16 <= len(abstract) <= 2048:
                score += 1
            else:
                comments.append(f'Line {a.sourceline}: is not between 16 and 2048 characters')

            LOGGER.debug('Testing for HTML detection')
            if not bool(BeautifulSoup(abstract, "html.parser").find()):
                score += 1
            else:
                comments.append(f'Line {a.sourceline}: contains markup')

            LOGGER.debug('Testing for bulletin headers')
            has_bulletin_header = re.search(r'[A-Z]{4}\d{2}[\s_]*[A-Z]{4}', abstract)
            if not has_bulletin_header:
                score += 1
            else:
                comments.append(f'Line {a.sourceline}: contains bulletin header')

            LOGGER.debug('Testing for spelling')
            misspelled = check_spelling(abstract)

            if not misspelled:
                score += 1
            else:
                comments.append(f'Line {a.sourceline}: contains spelling errors {misspelled}')

        return name, total, score, comments

    def kpi_004(self) -> tuple:
        """
        Implements KPI-4: Temporal information

        :returns: `tuple` of KPI name, achieved score, total score, and comments
        """

        total = 0
        score = 0
        comments = []
        time_periods = []

        name = 'KPI-4: Temporal information'

        LOGGER.info(f'Running {name}')

        time_period_xpath = '/gmd:MD_Metadata/gmd:identificationInfo//gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/gml:TimePeriod'

        try:
            LOGGER.debug(f'Testing for temporal information at "{time_period_xpath}"')
            time_periods = self.exml.xpath(time_period_xpath, namespaces=self.namespaces)
        except Exception as err:
            LOGGER.debug(err)

        if len(time_periods) > 0:
            for time_period in time_periods:
                total += 3
                score += 1
                begin_position = time_period.find(nspath_eval('gml:beginPosition'))
                end_position = time_period.find(nspath_eval('gml:endPosition'))
                if begin_position is not None and end_position is not None:
                    score += 1
                    dt_begin = parse_time_position(begin_position)
                    dt_end = parse_time_position(end_position)
                    if dt_begin is not None and dt_end is not None:
                        if dt_begin < dt_end:
                            score += 1
                            LOGGER.debug(f'Temporal information is valid ({dt_begin} < {dt_end}).')
                        else:
                            comments.append(f'Line {begin_position.sourceline}-{end_position.sourceline}: Temporal information is invalid ({dt_begin} < {dt_end} = False).')
                    elif dt_begin is None:
                        comments.append(f'Line {begin_position.sourceline}: Temporal information - begin time has unknown format')
                    elif dt_end is None:
                        comments.append(f'Line {end_position.sourceline}: Temporal information - end time has unknown format')
                elif begin_position is None:
                    comments.append(f'Line {time_period.sourceline}: Temporal information - begin time not found')
                elif end_position is None:
                    comments.append(f'Line {time_period.sourceline}: Temporal information - end time not found')
        else:
            total += 3
            comments.append('Temporal information not found')
        # I would be a bit confused by a product that spans multiple time_periods
        if len(time_periods) > 1:
            LOGGER.debug(f'Temporal information - multiple ({len(time_period)}) elements found.')

        update_frequency_xpath = '/gmd:MD_Metadata/gmd:identificationInfo//gmd:resourceMaintenance//gmd:maintenanceAndUpdateFrequency'
        LOGGER.debug(f'Testing for update frequency at "{update_frequency_xpath}"')
        total += 1
        update_frequency = self.exml.xpath(update_frequency_xpath, namespaces=self.namespaces)
        if len(update_frequency) > 0:
            score += 1
        else:
            comments.append('Update frequency not found')
        # grumble about extra elements
        if len(update_frequency) > 1:
            comments.append(f'Multiple ({len(update_frequency)}) update frequency elements found.')

        data_status_xpath = '/gmd:MD_Metadata/gmd:identificationInfo//gmd:status'
        LOGGER.debug(f'Testing for data status at "{data_status_xpath}"')
        total += 1
        data_status = self.exml.xpath(data_status_xpath, namespaces=self.namespaces)
        if len(data_status) > 0:
            score += 1
        else:
            comments.append('Data status not found')
        # I would be a bit confused by a product that has multiple data statuses
        if len(data_status) > 1:
            LOGGER.debug(f'Multiple ({len(data_status)}) data status elements found.')

        return name, total, score, comments

    def kpi_005(self) -> tuple:
        """
        Implements KPI-5: DOI citation

        :returns: `tuple` of KPI name, achieved score, total score, and comments
        """

        total = 0
        score = 0
        comments = []

        name = 'KPI-5: DOI citation'

        LOGGER.info(f'Running {name}')

        xpath = '//gmd:identificationInfo//gmd:citation//gmd:identifier//gmd:code/gmx:Anchor'

        LOGGER.debug(f'Testing all DOIs at {xpath}')

        doi_anchors = self.exml.xpath(xpath, namespaces=self.namespaces)

        if len(doi_anchors) > 0:
            doi_anchor = doi_anchors[0]
            LOGGER.debug('DOI anchor is present')
            # TODO: KPI def does not check for actual value
            total += 3
            score += 1

            LOGGER.debug('testing for DOI title')
            doi_title = doi_anchor.get(nspath_eval('xlink:title'))
            doi_text = doi_anchor.text

            if doi_title is not None and doi_title == 'DOI':
                score += 1
            else:
                comments.append('Line {doi_anchor.sourceline}: DOI title is not equal to "DOI"')

            xpath2 = '//gmd:identificationInfo//gmd:resourceConstraints//gmd:otherConstraints/gco:CharacterString'

            LOGGER.debug(f'Testing all DOIs in constraints at {xpath2}')

            doi_constraints = self.exml.xpath(xpath2, namespaces=self.namespaces)

            for d in doi_constraints:
                doi_constraint = d.text
                if doi_constraint is not None:
                    if 'Cite as:' in doi_constraint and doi_text in doi_constraint:
                        score += 1
                    else:
                        comments.append(f'Line {d.sourceline}: citation should start with "Cite as" and have matching DOI')

        return name, total, score, comments

    def kpi_006(self) -> tuple:
        """
        Implements KPI-6: Keywords

        :returns: `tuple` of KPI name, achieved score, total score, and comments
        """

        total = 0
        score = 0
        comments = []

        name = 'KPI-6: Keywords'

        LOGGER.info(f'Running {name}')

        LOGGER.debug('Testing whether any keyword is present')
        keywords_xpath = '//gmd:MD_DataIdentification/gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:keyword'
        keywords = self.exml.xpath(keywords_xpath, namespaces=self.namespaces)

        total += 1

        if len(keywords) > 0:
            score += 1
            LOGGER.debug(f'Found {len(keywords)} keywords')
        else:
            comments.append('No keywords found')

        LOGGER.debug('Evaluating keywords')
        total += 3
        keyword_count = 0
        anchor_keyword_count = 0
        string_keyword_count = 0
        keyword_with_type_count = 0
        keyword_with_thesaurus_count = 0

        keyword_toplevel_xpath = '//gmd:MD_DataIdentification/gmd:descriptiveKeywords/gmd:MD_Keywords'
        main_keyword_elements = self.exml.xpath(keyword_toplevel_xpath, namespaces=self.namespaces)

        for main_keyword in main_keyword_elements:
            keywords, types, thesauruses = get_keyword_info(main_keyword)
            keyword_count += len(keywords)
            # all keywords in this group have the same type
            if len(types) > 0:
                keyword_with_type_count += len(keywords)
            # all keywords in this group have the same thesaurus
            if len(thesauruses) > 0:
                keyword_with_thesaurus_count += len(keywords)
            bare_charstring_values = []
            for keyword in keywords:
                if len(types) == 0:
                    keywords_values = get_string_or_anchor_value(keyword)
                    LOGGER.debug(f'Line {keyword.sourceline}: Found keyword without type: {keywords_values}')
                if len(thesauruses) == 0:
                    keywords_values = get_string_or_anchor_value(keyword)
                    LOGGER.debug(f'Line {keyword.sourceline}: Found keyword without thesaurus: {keywords_values}')
                string_elements = keyword.findall(nspath_eval('gco:CharacterString'))
                anchor_elements = keyword.findall(nspath_eval('gmx:Anchor'))
                if len(string_elements) == 0 and len(anchor_elements) >= 0:
                    anchor_keyword_count += 1
                else:
                    string_keyword_count += 1
                    bare_charstring_values += [x.text for x in string_elements]
            if len(bare_charstring_values) > 0:
                LOGGER.debug(f'Found keywords that are bare character strings: {bare_charstring_values}')
        # final evaluation
        LOGGER.debug(f'Found {string_keyword_count} string and {anchor_keyword_count} anchor keywords')
        if anchor_keyword_count >= keyword_count:
            score += 1
            LOGGER.debug('All keywords are anchors')
        else:
            comments.append(f'Found {keyword_count - anchor_keyword_count} keywords that are not gmx:Anchor but a bare character string')

        if keyword_with_type_count >= keyword_count:
            score += 1
            LOGGER.debug('All keywords have a type definition')
        else:
            comments.append(f'Found {keyword_count - keyword_with_type_count} keywords without type definition')

        if keyword_with_thesaurus_count >= keyword_count:
            score += 1
            LOGGER.debug('All keywords have a thesaurus definition')
        else:
            comments.append(f'Found {keyword_count - keyword_with_thesaurus_count} keywords without thesaurus')

        return name, total, score, comments

    def kpi_007(self) -> tuple:
        """
        Implements KPI-7: Graphic overview for non bulletins metadata records

        :returns: `tuple` of KPI name, achieved score, total score, and comments
        """

        name = 'KPI-7: Graphic overview for non bulletins metadata records'

        LOGGER.info(f'Running {name}')

        total = 0
        score = 0
        comments = []

        web_image_mime_types = [
            'image/apng',
            'image/avif',
            'image/gif',
            'image/jpeg',
            'image/png',
            'image/svg+xml',
            'image/webp'
        ]

        xpath = '//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:graphicOverview/gmd:MD_BrowseGraphic/gmd:fileName'

        LOGGER.debug(f'Testing all graphic overviews at {xpath}')

        graphic_overviews = self.exml.xpath(xpath, namespaces=self.namespaces)

        LOGGER.info(graphic_overviews)

        if graphic_overviews:
            LOGGER.debug('Graphic overview is present')
            total = 3
            score += 1
            graphic_overview = graphic_overviews[0]
            anchors = graphic_overview.findall(nspath_eval('gmx:Anchor'))
            link = ''
            if anchors:
                link = anchors[0].get(nspath_eval('xlink:href'))
            else:
                character_strings = graphic_overview.findall(nspath_eval('gco:CharacterString'))
                if character_strings:
                    link = character_strings[0].text

            result = check_url(link, False)

            LOGGER.debug('Testing whether link resolves successfully')
            if result['accessible']:
                score += 1
            else:
                comments.append(f'Line {graphic_overview.sourceline}: URL not accessible: {link}')

            LOGGER.debug('Testing whether link is a web image file type')
            if result['mime-type'] in web_image_mime_types:
                score += 1
            else:
                comments.append(f'Line {graphic_overview.sourceline}: MIME type not a web image: {result["mime-type"]}')

        return name, total, score, comments

    def kpi_008(self) -> tuple:
        """
        Implements KPI-8: Links health

        Extracts URLs from various types of "links" in the metadata document and tries
        to download the linked resources. Resources are expected to be accessible, preferably over HTTPS.

        :returns: `tuple` of KPI name, achieved score, total score, and comments
        """

        name = 'KPI-8: Links health'

        LOGGER.info(f'Running {name}')

        total = 0
        score = 0
        comments = []

        links = self._get_link_lists()

        LOGGER.debug(f'Found {len(links)} unique links.')
        LOGGER.debug(f'{links}')

        for link in links:
            LOGGER.debug(f'checking: {link}')
            result = check_url(link, False)
            total += 2
            if result['accessible']:
                score += 1
                if result.get('url-resolved') != link:
                    LOGGER.debug(f'"{link}" resolves to "{result["url-resolved"]}"')
                if result.get('ssl'):
                    score += 1
                    LOGGER.debug(f'"{result["url-resolved"]}" is a valid HTTPS link')
                else:
                    LOGGER.debug(f'"{result["url-resolved"]}" is a valid link')
            else:
                msg = f'"{link}" cannot be resolved!'
                LOGGER.info(msg)
                comments.append(msg)

        return name, total, score, comments

    def kpi_009(self) -> tuple:
        """
        Implements KPI-9: Data policy

        :returns: `tuple` of KPI name, achieved score, total score, and comments
        """

        name = 'KPI-9: Data policy'

        LOGGER.info(f'Running {name}')

        total = 0
        score = 0
        comments = []

        data_policy_xpath = 'gmd:identificationInfo//gmd:resourceConstraints/gmd:MD_LegalConstraints/gmd:otherConstraints'
        license_codes = self.codelists['wmo']['WMO_DataLicenseCode']

        LOGGER.debug('Checking if data policy is a known value')

        total += 1

        data_license_code_is_anchor = False
        constraints = self.exml.findall(nspath_eval(data_policy_xpath))
        checked_values = []

        for constraint in constraints:
            value_elements = constraint.findall(nspath_eval('gco:CharacterString')) \
                + constraint.findall(nspath_eval('gmx:Anchor'))
            for element in value_elements:
                if element.text in license_codes:
                    score += 1
                    LOGGER.debug(f'Found {element.text}')
                    if 'Anchor' in element.tag:
                        data_license_code_is_anchor = True
                    else:
                        comments.append(f'Line {element.sourceline}: WMO_DataLicenseCode is not defined as an anchor')
                else:
                    checked_values.append(element.text)

        if score == 0:
            comments.append(f'None of {checked_values} is a known WMO_DataLicenseCode value')

        total += 1
        constraints_base_xpath = 'gmd:identificationInfo//gmd:resourceConstraints/gmd:MD_LegalConstraints/'
        constraints_elements = ['gmd:accessConstraints', 'gmd:useConstraints']
        other_restrictions_count = 0

        for elemment_name in constraints_elements:
            xpath = constraints_base_xpath + elemment_name + '/gmd:MD_RestrictionCode'
            LOGGER.debug(f'Checking if {elemment_name} is "otherRestrictions"')
            constraints = self.exml.xpath(xpath, namespaces=self.namespaces)
            if len(constraints) > 0:
                for constraint in constraints:
                    if constraint.text == 'otherRestrictions':
                        other_restrictions_count += 1
                        LOGGER.debug(f'Found {constraint.text}')
                    else:
                        comments.append(f'Line {constraint.sourceline}: Unexpected value at {xpath}: {constraint.text}')
            else:
                comments.append(f'Legal constraint {elemment_name} not found')
        if other_restrictions_count == len(constraints_elements):
            score += 1

        LOGGER.debug('Testing for definition of the distribution scope and product category')
        total += 3

        keyword_toplevel_xpath = '//gmd:MD_DataIdentification/gmd:descriptiveKeywords/gmd:MD_Keywords'
        main_keyword_elements = self.exml.xpath(keyword_toplevel_xpath, namespaces=self.namespaces)
        distribution_defined = False
        product_category_code_defined = False
        product_category_code_is_anchor = False
        distribution_scope_code_thesaurus_is_anchor = False

        for main_keyword in main_keyword_elements:
            keywords, types, thesauruses = get_keyword_info(main_keyword)
            if len(types) > 1:
                comments.append(f'Line {types[0].sourceline}: Ambiguous definition of keyword type ({types})')
            elif len(thesauruses) > 1:
                comments.append(f'Line {thesauruses[0].sourceline}: Ambiguous definition of thesaurus ({len(thesauruses)})')
            elif len(types) == 0 or len(thesauruses) == 0:
                continue

            thesaurus_title_values = get_string_or_anchor_value(thesauruses[0])
            if len(thesaurus_title_values) > 1:
                comments.append(f'Line {thesauruses[0].sourceline}: Ambiguous definition of thesaurus title ({thesaurus_title_values})')
            elif len(thesaurus_title_values) == 0:
                LOGGER.debug(f'Unnamed thesaurus of type {types[0]} at {thesauruses[0].sourceline}')
                continue

            if types[0] in self.codelists['wmo']['MD_KeywordTypeCode'] + self.codelists['iso']['MD_KeywordTypeCode']:
                thesaurus_name = thesaurus_title_values[0]
                LOGGER.debug(f'Found keyword type "{types[0]}" of "{thesaurus_name}"')
                if types[0] in ['dataCenter', 'dataCentre'] and 'WMO_DistributionScopeCode' == thesaurus_name:
                    LOGGER.debug(f'Found WMO_DistributionScopeCode {thesaurus_name}')
                    distribution_defined = True
                if 'WMO_DistributionScopeCode' == thesaurus_name:
                    for keyword in keywords:
                        value_elements = keyword.findall(nspath_eval('gco:CharacterString')) + keyword.findall(nspath_eval('gmx:Anchor'))
                        for element in value_elements:
                            value = element.text
                            if value in self.codelists['wmo']['WMO_DistributionScopeCode']:
                                if value in ['GlobalExchange', 'RegionalExchange']:
                                    constraints_xpath = 'gmd:identificationInfo//gmd:resourceConstraints/gmd:MD_LegalConstraints/gmd:otherConstraints'
                                    constraints = get_string_or_anchor_values(self.exml.findall(nspath_eval(constraints_xpath)))
                                    for constraint in constraints:
                                        if constraint in self.codelists['wmo']['WMO_GTSProductCategoryCode']:
                                            LOGGER.debug(f'Found {value} with product category "{constraint}"')
                                            product_category_code_defined = True
                                        # this was originally 'KPI-5: WMOEssential data links'
                                        if constraint == 'WMOEssential':
                                            LOGGER.debug(f'Is {constraint}')
                                            total += 1
                                            linkage_xpath = 'gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource/gmd:linkage'
                                            linkages = self.exml.xpath(linkage_xpath, namespaces=self.namespaces)
                                            if len(linkages) > 0:
                                                score += 1
                                                LOGGER.debug(f'Found {len(linkages)} online resource linkage(s)')
                                            else:
                                                comments.append('Resource transferOption link not found for WMOEssential data')
                                if 'Anchor' in element.tag:
                                    product_category_code_is_anchor = True
                                else:
                                    comments.append(f'Line {element.sourceline}: WMO_DistributionScopeCode is not defined as an anchor')
                                break
                    thesaurus_title_anchors = main_keyword.findall(nspath_eval('gmd:thesaurusName/gmd:CI_Citation/gmd:title/gmx:Anchor'))
                    if len(thesaurus_title_anchors) == 0:
                        comments.append(f'Line {thesauruses[0].sourceline}: WMO_DistributionScopeCode thesaurus title is not defined as an anchor')
                    else:
                        distribution_scope_code_thesaurus_is_anchor = True

        if distribution_defined:
            score += 1
        else:
            comments.append('No definition of the distribution scope found (keyword from WMO_DistributionScopeCode thesaurus)')

        if product_category_code_defined:
            score += 1
        else:
            comments.append('No product category code defined for globally or regionally exchanged data (keyword from WMO_GTSProductCategoryCode code list)')

        if data_license_code_is_anchor and product_category_code_is_anchor and distribution_scope_code_thesaurus_is_anchor:
            score += 1
        return name, total, score, comments

    def kpi_010(self) -> tuple:
        """
        Implements KPI-10: Distribution information

        :returns: `tuple` of KPI name, achieved score, total score, and comments
        """

        name = 'KPI-10: Distribution information'

        LOGGER.info(f'Running {name}')

        total = 5
        score = 0
        comments = []

        LOGGER.debug('Testing for distribution format')
        format_xpath = '//gmd:distributionInfo//gmd:distributionFormat/gmd:MD_Format'
        if self.exml.xpath(format_xpath, namespaces=self.namespaces):
            score += 1
            LOGGER.debug('Testing for a valid format specification')
            xpath = '//gmd:distributionInfo//gmd:distributionFormat/gmd:MD_Format//gmd:specification/gmx:Anchor'
            specification_url = self.exml.xpath(xpath, namespaces=self.namespaces)
            if specification_url:
                link = specification_url.get(nspath_eval('xlink:href'))
                result = check_url(link, False)

                if result['accessible']:
                    score += 1
                else:
                    comments.append(f'Line {specification_url.sourceline}: The format specification URL is not accessible: {link}')
            else:
                comments.append(f'Format URL is missing (expected at {xpath})')
        else:
            comments.append(f'Distribution format not found (expected at {format_xpath})')

        LOGGER.debug('Testing for distributor contact organization')
        xpath = '//gmd:distributionInfo//gmd:MD_Distributor//gmd:organisationName/gco:CharacterString'
        organization_name = self.exml.xpath(xpath, namespaces=self.namespaces)
        if organization_name:
            LOGGER.debug(f'Distribution contact organization found: {organization_name[0].text}')
            score += 1
        else:
            comments.append(f'Distribution contact organization not found (expected at {xpath})')

        LOGGER.debug('Testing for distributor contact email')
        xpath = '//gmd:distributionInfo//gmd:MD_Distributor//gmd:contactInfo//gmd:electronicMailAddress/gco:CharacterString'
        organization_email = self.exml.xpath(xpath, namespaces=self.namespaces)
        if organization_email:
            LOGGER.debug(f'Distribution contact email found: {organization_email[0].text}')
            score += 1
        else:
            comments.append(f'Distribution contact email not found (expected at {xpath})')

        LOGGER.debug('Testing for transfer options')
        xpath = '//gmd:distributionInfo//gmd:MD_DigitalTransferOptions//gmd:onLine//gmd:URL'
        transfer_options = [x for x in self.exml.xpath(xpath, namespaces=self.namespaces)]
        if len(transfer_options) > 0:
            LOGGER.debug(f'Transfer options found: {len(transfer_options)}')
            score += 1
        else:
            comments.append(f'No transfer options found (expected at {xpath})')

        return name, total, score, comments

    def kpi_011(self) -> tuple:
        """
        Implements KPI-11: Codelists validation

        :returns: `tuple` of KPI name, achieved score, total score, and comments
        """

        total = 0
        score = 0
        comments = []

        name = 'KPI-11: Codelists validation'

        LOGGER.info(f'Running {name}')

        xpaths = {
            'wmo': [
                '//gmd:date/gmd:CI_Date/gmd:dateType/gmd:CI_DateTypeCode',
                '//gmd:MD_Keywords/gmd:type/gmd:MD_KeywordTypeCode'
            ],
            'iso': [
                '//gmd:CI_ResponsibleParty/gmd:role/gmd:CI_RoleCode',
                '//gmd:resourceConstraints//gmd:MD_RestrictionCode',
                '//gmd:scope//gmd:MD_ScopeCode',
            ]
        }

        xpaths2 = [
            '//gmd:resourceConstraints//gmd:otherConstraints',
            '//gmd:resourceConstraints//gmd:otherConstraints',
            '//gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:keyword'
        ]

        for key, values in xpaths.items():
            LOGGER.debug(f'Evaluating {key} codelist values')
            for xpath in values:
                LOGGER.debug(f'Evaluating {xpath}')
                for xpath2 in self.exml.xpath(xpath, namespaces=self.namespaces):
                    total += 1
                    try:
                        codelist = xpath2.attrib.get('codeList').split('#')[-1]
                        LOGGER.debug(f'Checking {codelist}')
                        if xpath2.text in self.codelists[key][codelist]:
                            score += 1
                        else:
                            comments.append(f"Line {xpath2.sourceline}: Invalid codelist value: '{xpath2.text}' not in '{codelist}'")
                    except AttributeError:
                        comments.append(f"Line {xpath2.sourceline}: Missing codeList attribute: '{xpath2.text}'")
                    except KeyError:
                        comments.append(f"Line {xpath2.sourceline}: Invalid code list reference: '{codelist}' is not defined in '{key}'")

        xpath = '//gmd:topicCategory/gmd:MD_TopicCategoryCode'

        LOGGER.debug(f'Evaluating {xpath}')
        for xpath2 in self.exml.xpath(xpath, namespaces=self.namespaces):
            total += 1
            if xpath2.text in self.codelists['iso']['MD_TopicCategoryCode']:
                score += 1
            else:
                comments.append(f'Line {xpath2.sourceline}: Invalid codelist value: {xpath2.text} not in MD_TopicCategoryCode')

        codelists2 = self.codelists['wmo']['WMO_GTSProductCategoryCode'] + \
            self.codelists['wmo']['WMO_CategoryCode'] + \
            self.codelists['wmo']['WMO_DistributionScopeCode']

        for xpath2 in xpaths2:
            LOGGER.debug(f'Evaluating {xpath2}')
            values = get_string_or_anchor_values(self.exml.findall(nspath_eval(xpath2)))
            for value in values:
                if value in codelists2:
                    total += 1
                    score += 1

        return name, total, score, comments

    def evaluate(self, kpi: int = 0) -> dict:
        """
        Convenience function to run all tests

        :returns: `dict` of overall test report
        """

        known_kpis = [
            'kpi_001',
            'kpi_002',
            'kpi_003',
            'kpi_004',
            'kpi_005',
            'kpi_006',
            'kpi_007',
            'kpi_008',
            'kpi_009',
            'kpi_010',
            'kpi_011'
        ]

        kpis_to_run = known_kpis

        if kpi != 0:
            selected_kpi = f'kpi_{kpi:03}'
            if selected_kpi not in known_kpis:
                msg = f'Invalid KPI number: {selected_kpi} is not in {known_kpis}'
                LOGGER.error(msg)
                raise ValueError(msg)
            else:
                kpis_to_run = [selected_kpi]

        LOGGER.info(f'Evaluating KPIs: {kpis_to_run}')

        results = {}

        for kpi in kpis_to_run:
            LOGGER.debug(f'Running {kpi}')
            result = getattr(self, kpi)()
            LOGGER.debug(f'Raw result: {result}')
            LOGGER.debug('Calculating result')
            try:
                percentage = round(float((result[2] / result[1]) * 100), ROUND)
            except ZeroDivisionError:
                percentage = None

            results[kpi] = {
                'name': result[0],
                'total': result[1],
                'score': result[2],
                'comments': result[3],
                'percentage': percentage
            }
            LOGGER.debug(f'{kpi}: {result[1]} / {result[2]} = {percentage}')

        # the summary only if more than one KPI was evaluated
        if len(kpis_to_run) > 1:
            LOGGER.debug('Calculating total results')
            results['summary'] = generate_summary(results)
            # this total summary needs extra elements
            results['summary']['identifier'] = self.identifier,
            overall_grade = 'F'
            if results['kpi_001']['percentage'] != 100:
                overall_grade = 'U'
            else:
                overall_grade = calculate_grade(results['summary']['percentage'])
            results['summary']['grade'] = overall_grade

        return results


def generate_summary(results: dict) -> dict:
    """
    Genrerates a summary entry for given group of results

    :param results: results to generate the summary from
    """

    sum_total = sum(v['total'] for v in results.values())
    sum_score = sum(v['score'] for v in results.values())
    comments = {k: v['comments'] for k, v in results.items() if v['comments']}

    try:
        sum_percentage = round(float((sum_score / sum_total) * 100), ROUND)
    except ZeroDivisionError:
        sum_percentage = None

    summary = {
        'total': sum_total,
        'score': sum_score,
        'comments': comments,
        'percentage': sum_percentage,
    }

    return summary


def calculate_grade(percentage: float) -> str:
    """
    Calculates letter grade from numerical score

    :param percentage: float between 0-100
    """

    if percentage is None:
        grade = None
    elif percentage > 100 or percentage < 0:
        raise ValueError('Invalid percentage')
    elif percentage >= 80:
        grade = 'A'
    elif percentage >= 65:
        grade = 'B'
    elif percentage >= 50:
        grade = 'C'
    elif percentage >= 35:
        grade = 'D'
    elif percentage >= 20:
        grade = 'E'

    return grade


def group_kpi_results(kpis_results: dict) -> dict:
    """
    Groups KPI results by category

    :param kpis_results: `dict` of the results to be grouped
    """

    grouped_kpi_results = {}
    grouped_kpi_results['mandatory'] = {k: kpis_results[k] for k in ['kpi_001']}

    content_information = {f'kpi_{k:03}': kpis_results[f'kpi_{k:03}'] for k in [2, 3, 4, 5, 6, 7]}
    grouped_kpi_results['content_information'] = content_information
    grouped_kpi_results['content_information']['summary'] = generate_summary(content_information)

    distribution_information = {f'kpi_{k:03}': kpis_results[f'kpi_{k:03}'] for k in [9, 10]}
    grouped_kpi_results['distribution_information'] = distribution_information
    grouped_kpi_results['distribution_information']['summary'] = generate_summary(distribution_information)

    enhancements = {f'kpi_{k:03}': kpis_results[f'kpi_{k:03}'] for k in [8, 11]}
    grouped_kpi_results['enhancements'] = enhancements
    grouped_kpi_results['enhancements']['summary'] = generate_summary(enhancements)

    # copy the total summary as-is
    if kpis_results['summary']:
        grouped_kpi_results['summary'] = kpis_results['summary']

    return grouped_kpi_results
