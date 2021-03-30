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
# Copyright (c) 2020-2021 Government of Canada
# Copyright (c) 2020-2021 IBL Software Engineering spol. s r. o.
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

# WMO Core Metadata Profile Key Performance Indicators (KPIs)

from itertools import chain
from io import BytesIO
import json
import logging
import re

from bs4 import BeautifulSoup
import click
from lxml import etree
from spellchecker import SpellChecker

from pywcmp.ats import TestSuiteError, WMOCoreMetadataProfileTestSuite13
from pywcmp.util import (get_cli_common_options, get_codelists, nspath_eval,
                         parse_time_position, setup_logger, urlopen_, check_url)

LOGGER = logging.getLogger(__name__)
# round percentages to x decimal places
ROUND = 3


class WMOCoreMetadataProfileKeyPerformanceIndicators:
    """Key Performance Indicators for WMO Core Metadata Profile"""

    def __init__(self, exml):
        """
        initializer

        :param exml: `etree.ElementTree` object

        :returns: `pywcmp.kpi.WMOCoreMetadataProfileKeyPerformanceIndicators`
        """

        self.exml = exml  # serialized already
        self.namespaces = self.exml.getroot().nsmap

        # generate dict of codelists
        self.codelists = get_codelists()

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
        LOGGER.debug('Running ATS tests')
        ts = WMOCoreMetadataProfileTestSuite13(self.exml)

        total = 1
        comments = []

        # run the tests
        try:
            ts.run_tests()
            score = 1
        except TestSuiteError as err:
            score = 0
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

        titles = [x.text for x in self.exml.xpath(xpath, namespaces=self.namespaces)]

        for title in titles:
            LOGGER.debug('Title is present')
            total += 8
            score += 1

            LOGGER.debug('Testing number of words')
            title_words = title.split()
            if len(title_words) >= 3:
                score += 1
            else:
                comments.append(f'{xpath} has less than 3 words')

            LOGGER.debug('Testing number of characters')
            if len(title) <= 150:
                score += 1
            else:
                comments.append(f'{xpath} has more than 150 characters')

            LOGGER.debug('Testing for alphanumeric characters')
            if title.isalnum():
                score += 1
            else:
                comments.append(f'{xpath} contains non-printable characters')

            LOGGER.debug('Testing for title case')
            if title.istitle():
                score += 1
            else:
                comments.append(f'{xpath} is not title case')

            LOGGER.debug('Testing for acronyms')
            if len(re.findall(r'([A-Z]\.*){2,}s?', title)) <= 3:
                score += 1
            else:
                comments.append(f'{xpath} has more than 3 acronyms')

            LOGGER.debug('Testing for bulletin headers')
            has_bulletin_header = re.search(r'[A-Z]{4}\d{2}[\s_]*[A-Z]{4}', title)
            if not has_bulletin_header:
                score += 1
            else:
                score -= 1
                comments.append(f'{xpath} contains bulletin header')

            LOGGER.debug('Testing for spelling')
            spell = SpellChecker()
            misspelled = spell.unknown(title_words)

            if not misspelled:
                score += 1
            else:
                comments.append(f'{xpath} contains spelling errors {misspelled}')

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

        abstracts = [x.text for x in self.exml.xpath(xpath, namespaces=self.namespaces)]

        for abstract in abstracts:
            LOGGER.debug('Abstract is present')
            total += 3
            score += 1

            LOGGER.debug('Testing number of characters')
            if 16 <= len(abstract) <= 2048:
                score += 1
            else:
                comments.append(f'{xpath} is not between 16 and 2048 characters')

            LOGGER.debug('Testing for HTML detection')
            if not bool(BeautifulSoup(abstract, "html.parser").find()):
                score += 1
            else:
                comments.append(f'{xpath} contains markup')

            LOGGER.debug('Testing for bulletin headers')
            has_bulletin_header = re.search(r'[A-Z]{4}\d{2}[\s_]*[A-Z]{4}', abstract)
            if not has_bulletin_header:
                score += 1
            else:
                score -= 1
                comments.append(f'{xpath} contains bulletin header')

            LOGGER.debug('Testing for spelling')
            spell = SpellChecker()
            misspelled = spell.unknown(abstract.split())

            if not misspelled:
                score += 1
            else:
                comments.append(f'{xpath} contains spelling errors {misspelled}')

        return name, total, score, comments

    def kpi_004(self) -> tuple:
        """
        Implements KPI-4: Temporal information

        :returns: `tuple` of KPI name, achieved score, total score, and comments
        """

        total = 0
        score = 0
        comments = []

        name = 'KPI-4: Temporal information'

        LOGGER.info(f'Running {name}')

        time_period_xpath = '/gmd:MD_Metadata/gmd:identificationInfo//gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/gml:TimePeriod'
        LOGGER.debug(f'Testing for temporal information at "{time_period_xpath}"')
        time_periods = self.exml.xpath(time_period_xpath, namespaces=self.namespaces)
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
                            comments.append(f'Temporal information is invalid ({dt_begin} < {dt_end} = False).')
                    elif dt_begin is None:
                        comments.append('Temporal information - begin time has unknown format')
                    elif dt_end is None:
                        comments.append('Temporal information - end time has unknown format')
                elif begin_position is None:
                    comments.append('Temporal information - begin time not found')
                elif end_position is None:
                    comments.append('Temporal information - end time not found')
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

        xpath = '//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:graphicOverview/gmd:MD_BrowseGraphic/gmd:fileName/gmx:Anchor'

        LOGGER.debug(f'Testing all graphic overviews at {xpath}')

        graphic_overviews = [x for x in self.exml.xpath(xpath, namespaces=self.namespaces)]

        for graphic_overview in graphic_overviews:
            LOGGER.debug('Graphic overview is present')
            total += 3
            score += 1

            link = graphic_overview.get(nspath_eval('xlink:href'))
            result = check_url(link, False)

            LOGGER.debug('Testing whether link resolves successfully')
            if result['accessible']:
                score += 1
            else:
                comments.append(f'URL not accessible: {link}')

            LOGGER.debug('Testing whether link is a web image file type')
            if result['mime-type'] in web_image_mime_types:
                score += 1
            else:
                comments.append(f'MIME type not a web image: {result["mime-type"]}')

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
                if result.get('ssl') is True:
                    score += 1
                    LOGGER.debug(f'"{result["url-resolved"]}" is a valid HTTPS link')
                else:
                    LOGGER.debug(f'"{result["url-resolved"]}" is a valid link')
            else:
                msg = f'"{link}" cannot be resolved!'
                LOGGER.info(msg)
                comments.append(msg)

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

        xpath = '//gmd:distributionInfo'

        LOGGER.debug('Testing for distribution format')
        xpath = '//gmd:distributionInfo//gmd:distributionFormat/gmd:MD_Format'
        if self.exml.xpath(xpath, namespaces=self.namespaces):
            score += 1
        else:
            comments.append('Distribution format not found')

        LOGGER.debug('Testing for a valid format specification')
        xpath = '//gmd:distributionInfo//gmd:distributionFormat/gmd:MD_Format//gmd:specification/gmx:Anchor'
        specification_url = self.exml.xpath(xpath, namespaces=self.namespaces)
        if specification_url:
            link = specification_url.get(nspath_eval('xlink:href'))
            result = check_url(link, False)

            if result['accessible']:
                score += 1
            else:
                comments.append(f'Specification URL not accessible: {link}')
        else:
            comments.append('Specification URL does not exist')

        LOGGER.debug('Testing for distributor contact organization')
        xpath = '//gmd:distributionInfo//gmd:MD_Distributor//gmd:organisationName/gco:CharacterString'
        organization_name = self.exml.xpath(xpath, namespaces=self.namespaces)
        if organization_name:
            LOGGER.debug(f'Distribution contact organization found: {organization_name[0].text}')
            score += 1
        else:
            comments.append('Distribution contact organization not found')

        LOGGER.debug('Testing for distributor contact email')
        xpath = '//gmd:distributionInfo//gmd:MD_Distributor//gmd:contactInfo//gmd:electronicMailAddress/gco:CharacterString'
        organization_email = self.exml.xpath(xpath, namespaces=self.namespaces)
        if organization_email:
            LOGGER.debug(f'Distribution contact email found: {organization_email[0].text}')
            score += 1
        else:
            comments.append('Distribution contact email not found')

        LOGGER.debug('Testing for transfer options')
        xpath = '//gmd:distributionInfo//gmd:MD_DigitalTransferOptions//gmd:onLine//gmd:URL'
        transfer_options = [x for x in self.exml.xpath(xpath, namespaces=self.namespaces)]
        if len(transfer_options) > 0:
            LOGGER.debug(f'Transfer options found: {len(transfer_options)}')
            score += 1
        else:
            comments.append('No transfer options found')

        return name, total, score, comments

    def kpi_012(self) -> tuple:
        """
        Implements KPI-12: DOI citation

        :returns: `tuple` of KPI name, achieved score, total score, and comments
        """

        total = 3
        score = 0
        comments = []

        name = 'KPI-12: DOI citation'

        LOGGER.info(f'Running {name}')

        xpath = '//gmd:identificationInfo//gmd:citation//gmd:identifier//gmd:code/gmx:Anchor'

        LOGGER.debug(f'Testing all DOIs at {xpath}')

        doi_anchors = self.exml.xpath(xpath, namespaces=self.namespaces)

        for doi_anchor in doi_anchors:
            LOGGER.debug('DOI anchor is present')
            # TODO: KPI def does not check for actual value
            score += 3
            score += 1

            LOGGER.debug('testing for DOI title')
            doi_title = doi_anchor.get(nspath_eval('xlink:title'))
            doi_text = doi_anchor.text

            if doi_title is not None and doi_title == 'DOI':
                score += 1
            else:
                comments.append('DOI title is not equal to "DOI"')

            xpath2 = '//gmd:identificationInfo//gmd:resourceConstraints//gmd:otherConstraints/gco:CharacterString'

            LOGGER.debug(f'Testing all DOIs in constraints at {xpath2}')

            doi_constraints = [x.text for x in self.exml.xpath(xpath2, namespaces=self.namespaces)]

            for doi_constraint in doi_constraints:
                if 'Cite as:' in doi_constraint and doi_text in doi_constraint:
                    score += 1
                else:
                    comments.append('citation should start with "Cite as" and have matching DOI')

        return name, total, score, comments

    def evaluate(self) -> dict:
        """
        Convenience function to run all tests

        :returns: `dict` of overall test report
        """

        kpis_to_run = [
            'kpi_001',
            'kpi_002',
            'kpi_003',
            'kpi_004',
            'kpi_007',
            'kpi_008',
            'kpi_010',
            'kpi_012'
        ]

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

        LOGGER.debug('Calculating total results')
        sum_total = sum(v['total'] for v in results.values())
        sum_score = sum(v['score'] for v in results.values())
        comments = [v['comments'] for v in results.values() if v['comments']]
        comments = list(chain(comments))
        sum_percentage = round(float((sum_score / sum_total) * 100), ROUND)

        results['summary'] = {
            'total': sum_total,
            'score': sum_score,
            'comments': comments,
            'percentage': sum_percentage
        }

        return results


@click.group()
def kpi():
    """key performance indicators"""
    pass


@click.command()
@click.pass_context
@get_cli_common_options
@click.option('--file', '-f', 'file_',
              type=click.Path(exists=True, resolve_path=True),
              help='Path to XML file')
@click.option('--summary', '-s', is_flag=True, default=False,
              help='Provide summary of KPI test results')
@click.option('--url', '-u',
              help='URL of XML file')
def validate(ctx, file_, summary, url, logfile, verbosity):
    """run key performance indicators"""

    if file_ is None and url is None:
        raise click.UsageError('Missing --file or --url options')

    setup_logger(verbosity, logfile)

    if file_ is not None:
        content = file_
        msg = f'Validating file {file_}'
        LOGGER.info(msg)
        click.echo(msg)
    elif url is not None:
        content = BytesIO(urlopen_(url).read())

    exml = etree.parse(content)

    kpis = WMOCoreMetadataProfileKeyPerformanceIndicators(exml)

    kpis_results = kpis.evaluate()

    if not summary:
        click.echo(json.dumps(kpis_results, indent=4))
    else:
        click.echo(json.dumps(kpis_results['summary'], indent=4))


kpi.add_command(validate)
