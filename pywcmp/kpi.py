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
# Copyright (c) 2020 IBL Software Engineering spol. s r. o.
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
import logging
from io import BytesIO

import click
from lxml import etree

from pywcmp.ats import TestSuiteError, WMOCoreMetadataProfileTestSuite13
from pywcmp.util import (get_cli_common_options, get_codelists, setup_logger,
                         urlopen_, check_url)

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

        :returns: `tuple` containing achieved score, total score, and comments
        """

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

        return total, score, comments

    def kpi_008(self) -> tuple:
        """
        Implements KPI-8: Links health

        Extracts URLs from various types of "links" in the metadata document and tries
        to download the linked resources. Resources are expected to be accessible, preferably over HTTPS.

        :returns: `tuple` containing achieved score, total score, and comments
        """

        total = 0
        score = 0
        comments = []

        links = self._get_link_lists()

        LOGGER.info(f'Found {len(links)} unique links.')
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

        return total, score, comments

    def evaluate(self) -> dict:
        """
        Convenience function to run all tests

        :returns: `dict` of overall test report
        """

        kpis_to_run = ['kpi_001', 'kpi_008']

        results = {}

        for kpi in kpis_to_run:
            LOGGER.debug(f'Running {kpi}')
            result = getattr(self, kpi)()
            LOGGER.debug('Calculating result')
            percentage = round(float((result[1] / result[0]) * 100), ROUND)

            results[kpi] = {
                'total': result[0],
                'score': result[1],
                'comments': result[2],
                'percentage': percentage
            }
            LOGGER.debug(f'{kpi}: {result[0]} / {result[1]} = {percentage}')

        LOGGER.debug('Calculating total results')
        sum_total = sum(v['total'] for v in results.values())
        sum_score = sum(v['score'] for v in results.values())
        comments = [v['comments'] for v in results.values() if v['comments']]
        comments = list(chain(comments))
        sum_percentage = round(float((sum_score / sum_total) * 100), ROUND)

        results['totals'] = {
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
@click.option('--url', '-u',
              help='URL of XML file')
def validate(ctx, file_, url, logfile, verbosity):
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

    click.echo(kpis.evaluate()['totals'])


kpi.add_command(validate)
