###############################################################################
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2024 Tom Kralidis
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

import logging
import mimetypes
import re
import uuid

from bs4 import BeautifulSoup

import pywcmp
from pywcmp.util import (check_spelling, check_url,
                         get_current_datetime_rfc3339)

LOGGER = logging.getLogger(__name__)

# round percentages to x decimal places
ROUND = 3


def gen_test_id(test_id: str) -> str:
    """
    Convenience function to print test identifier as URI

    :param test_id: test suite identifier

    :returns: test identifier as URI
    """

    return f'http://wis.wmo.int/spec/wcmp/2/kpi/core/{test_id}'


class WMOCoreMetadataProfileKeyPerformanceIndicators:
    """Key Performance Indicators for WMO Core Metadata Profile"""

    def __init__(self, data):
        """
        initializer

        :param data: dict of WCMP JSON

        :returns: `pywcmp.wcmp2.kpi.WMOCoreMetadataProfileKeyPerformanceIndicators`  # noqa
        """

        self.data = data
        self.codelists = None

    @property
    def identifier(self):
        """
        Helper function to derive a metadata record identifier

        :returns: metadata record identifier
        """

        return self.data['id']

    def kpi_title(self) -> tuple:
        """
        Implements KPI for Good quality title

        :returns: `tuple` of KPI id, title, achieved score, total score,
                  and comments
        """

        total = 8
        score = 0
        comments = []

        id_ = gen_test_id('good_quality_title')
        title = 'Good quality title'
        acronym_regex = r'\b([A-Z]{2,}\d*)\b'

        LOGGER.info(f'Running {title}')

        title = self.data['properties']['title']

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
            comments.append('Title has less than 3 words')

        LOGGER.debug('Testing number of characters')
        if len(title) <= 150:
            score += 1
        else:
            comments.append('Title has more than 150 characters')

        LOGGER.debug('Testing for alphanumeric characters')
        if all(x.isalnum() for x in title_words):
            score += 1
        else:
            comments.append('Title contains non-printable characters')

        LOGGER.debug('Testing for sentence case')
        title2 = re.sub(acronym_regex, '', title).strip()
        if title2.capitalize() == title2:
            score += 1
        else:
            comments.append('Title is not sentence case')

        LOGGER.debug('Testing for acronyms')

        if len(re.findall(acronym_regex, title)) <= 3:
            score += 1
        else:
            comments.append('Title has more than 3 acronyms')

        LOGGER.debug('Testing for bulletin headers')
        has_bulletin_header = re.search(r'[A-Z]{4}\d{2}[\s_]*[A-Z]{4}', title)
        if not has_bulletin_header:
            score += 1
        else:
            score -= 1
            comments.append('Title contains bulletin header')

        LOGGER.debug('Testing for spelling')
        misspelled = check_spelling(title)

        if not misspelled:
            score += 1
        else:
            comments.append(f'Title contains spelling errors {misspelled}')

        return id_, title, total, score, comments

    def kpi_description(self) -> tuple:
        """
        Implements KPI for Good quality description

        :returns: `tuple` of KPI id, title, achieved score, total score,
                  and comments
        """

        total = 4
        score = 0
        comments = []

        id_ = gen_test_id('good_quality_description')
        title = ': Good quality description'

        LOGGER.info(f'Running {title}')

        description = self.data['properties']['description']

        LOGGER.debug('Description is present')

        if description is None:
            comments.append('Description is null')

        LOGGER.debug('Testing number of characters')
        if 16 <= len(description) <= 2048:
            score += 1
        else:
            comments.append('Description is not between 16 and 2048 characters')  # noqa

        LOGGER.debug('Testing for HTML detection')
        if not bool(BeautifulSoup(description, "html.parser").find()):
            score += 1
        else:
            comments.append('Description contains markup')

        LOGGER.debug('Testing for bulletin headers')
        has_bulletin_header = re.search(r'[A-Z]{4}\d{2}[\s_]*[A-Z]{4}', description)  # noqa
        if not has_bulletin_header:
            score += 1
        else:
            comments.append('Description contains bulletin header')

        LOGGER.debug('Testing for spelling')
        misspelled = check_spelling(description)

        if not misspelled:
            score += 1
        else:
            comments.append(f'Description contains spelling errors {misspelled}')  # noqa

        return id_, title, total, score, comments

    def kpi_time_intervals(self) -> tuple:
        """
        Implements KPI for Time intervals

        :returns: `tuple` of KPI id, title, achieved score, total score,
                  and comments
        """

        time_intervals = []

        total = 0
        score = 0
        comments = []

        id_ = gen_test_id('time_intervals')
        title = 'Time intervals'

        LOGGER.info(f'Running {title}')

        time_ = self.data.get('time')
        if time_ is None:
            msg = 'time is null; no KPI check'
            LOGGER.debug(msg)
            return id_, title, 0, 0, [msg]

        interval = self.data['time'].get('interval')

        if interval is not None:
            time_intervals.append(self.data['time'])

        try:
            if self.data['additionalExtents']['temporal']['interval'] is not None:  # noqa
                time_intervals.append(
                    self.data['additionalExtents']['temporal'])
        except KeyError:
            pass

        for time_interval in time_intervals:
            total += 3

            interval = time_interval['interval']

            if '..' not in interval and interval[0] <= interval[1]:
                score += 1
            elif interval[1] == '..':
                score += 1
            else:
                comments.append('Begin must be less than or equal to the end or open')  # noqa

            if interval != ['..', '..']:
                score += 1
            else:
                comments.append('Temporal interval cannot be fully open')

            if time_interval.get('resolution') is not None:
                score += 1
            else:
                comments.append('No temporal resolution found')

        return id_, title, total, score, comments

    def kpi_graphic_overview(self) -> tuple:
        """
        Implements KPI for Graphic overview for metadata records

        :returns: `tuple` of KPI id, title, achieved score, total score,
                  and comments
        """

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

        id_ = gen_test_id('graphic_overview_for_metadata_records')
        title = 'Graphic overview for metadata records'

        LOGGER.info(f'Running {title}')

        for link in self.data['links']:
            if link.get('rel') == 'preview':
                LOGGER.debug('Found a preview link')

                total += 3
                score += 1

                result = check_url(link['href'], False)

                LOGGER.debug('Testing whether link is a web image file type')
                mime_type = link.get('type', '')
                if mime_type in web_image_mime_types and result['mime-type'] in web_image_mime_types:  # noqa
                    score += 1
                else:
                    comments.append(f'MIME type {mime_type} not a web image')

                LOGGER.debug('Testing whether link resolves successfully')
                if result['accessible']:
                    score += 1
                else:
                    comments.append(f"URL not accessible: {link['href']}")

        return id_, title, total, score, comments

    def kpi_links_health(self) -> tuple:
        """
        Implements KPI for Links health

        :returns: `tuple` of KPI id, title, achieved score, total score,
                  and comments
        """

        links = []

        total = 0
        score = 0
        comments = []

        id_ = gen_test_id('links_health')
        title = 'Links health'

        valid_link_mime_types = list(mimetypes.types_map.values())
        valid_link_mime_types.extend([
            'application/x-bufr',
            'application/x-grib',
            'text/turtle'
        ])

        LOGGER.info(f'Running {title}')

        LOGGER.debug('Assembling all links')

        links.extend([link for link in self.data['links']])

        for theme in self.data['properties']['themes']:
            for concept in theme['concepts']:
                if 'url' in concept:
                    links.append({
                        'href': concept['url']
                    })
            links.append({
                'href': theme.get('scheme')
            })

        for contact in self.data['properties']['contacts']:
            for link in contact.get('links', []):
                links.append({
                    'href': link['href']
                })

        for link in links:
            LOGGER.debug(f'Checking link: {link}')
            if link.get('href') is None:
                LOGGER.debug(f"URL is not a proper URL: {link['href']}")
                continue

            if link.get('href', '').startswith('http'):
                total += 2

                LOGGER.debug('Testing whether link resolves successfully')
                result = check_url(link['href'], False)

                if result['accessible']:
                    score += 1
                else:
                    comments.append(f"URL not accessible: {link['href']}")

                LOGGER.debug('Checking whether link has a valid media type')
                link_type = link.get('type')

                if link_type is None:
                    LOGGER.debug('Deriving link type from HTTP Content-Type')
                    link_type = result.get('mime-type')

                if link_type in valid_link_mime_types:
                    score += 1
                else:
                    comments.append(f"invalid link type {link_type}")

        return id_, title, total, score, comments

    def kpi_contacts(self) -> tuple:
        """
        Implements KPI for Contacts

        :returns: `tuple` of KPI id, title, achieved score, total score,
                  and comments
        """

        host_contact = None
        email_found = False

        total = 3
        score = 0
        comments = []

        id_ = gen_test_id('contacts')
        title = 'Contacts'

        LOGGER.info(f'Running {title}')

        for contact in self.data['properties']['contacts']:
            if 'host' in contact['roles']:
                host_contact = contact

        if host_contact is None:
            comments.append('No host contact found')
        else:
            score += 1

            if host_contact.get('contactInstructions') is None:
                comments.append('No host contact instructions found')
            else:
                score += 1

            for email in contact.get('emails', []):
                if 'value' in email:
                    email_found = True
                    break

            if email_found:
                score += 1
            else:
                comments.append('No host contact email found')

        return id_, title, total, score, comments

    def kpi_pids(self) -> tuple:
        """
        Implements KPI for Persistent identifiers

        :returns: `tuple` of KPI id, title, achieved score, total score,
                  and comments
        """

        doi_ark_hdl_found = False

        total = 0
        score = 0
        comments = []

        id_ = gen_test_id('persistent_identifiers')
        title = 'Persistent identifiers'

        LOGGER.info(f'Running {title}')

        if 'externalIds' in self.data['properties']:
            total = 3
            score += 1

            for external_id in self.data['properties']['externalIds']:
                if external_id['scheme'] in ['doi', 'ark', 'hdl']:
                    doi_ark_hdl_found = True

            if doi_ark_hdl_found:
                score += 1
            else:
                comments.append('No DOI/ARK/HDL schema found')

        for link in self.data['links']:
            if link.get('rel', '') == 'cite-as':
                score += 1
                break

        return id_, title, total, score, comments

    def evaluate(self, kpi: str = None) -> dict:
        """
        Convenience function to run all tests

        :param kpi: `str` of KPI identifier

        :returns: `dict` of overall test report
        """

        kpis_to_run = []

        for f in dir(WMOCoreMetadataProfileKeyPerformanceIndicators):
            if all([
                    callable(getattr(WMOCoreMetadataProfileKeyPerformanceIndicators, f)),  # noqa
                    f.startswith('kpi_')]):

                kpis_to_run.append(f)

        if kpi is not None:
            selected_kpi = f'kpi_{kpi}'
            if selected_kpi not in kpis_to_run:
                msg = f'Invalid KPI number: {selected_kpi} is not in {kpis_to_run}'  # noqa
                LOGGER.error(msg)
                raise ValueError(msg)
            else:
                kpis_to_run = [selected_kpi]

        LOGGER.info(f'Evaluating KPIs: {kpis_to_run}')

        results = {
            'id': str(uuid.uuid4()),
            'report_type': 'kpi',
            'metadata_id': self.identifier,
            'datetime': get_current_datetime_rfc3339(),
            'generated_by': f'pywcmp {pywcmp.__version__} (https://github.com/wmo-im/pywcmp)',  # noqa
            'tests': []
        }

        for kpi in kpis_to_run:
            LOGGER.debug(f'Running {kpi}')
            result = getattr(self, kpi)()
            LOGGER.debug(f'Raw result: {result}')
            LOGGER.debug('Calculating result')
            try:
                percentage = round(float((result[3] / result[2]) * 100), ROUND)
            except ZeroDivisionError:
                percentage = None

            results['tests'].append({
                'id': result[0],
                'title': result[1],
                'total': result[2],
                'score': result[3],
                'comments': result[4],
                'percentage': percentage
            })
            LOGGER.debug(f'{kpi}: {result[2]} / {result[3]} = {percentage}')

        LOGGER.debug('Calculating total results')
        results['summary'] = generate_summary(results)
        # this total summary needs extra elements
        overall_grade = 'F'
        overall_grade = calculate_grade(results['summary']['percentage'])
        results['summary']['grade'] = overall_grade

        return results


def generate_summary(results: dict) -> dict:
    """
    Generates a summary entry for given group of results

    :param results: results to generate the summary from

    :returns: `dict` of summary report
    """

    sum_total = sum(v['total'] for v in results['tests'])
    sum_score = sum(v['score'] for v in results['tests'])
    comments = {}

    for test in results['tests']:
        if test['comments']:
            for k, v in test.items():
                comments[k] = v

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

    :returns: `str` of calculated letter grade
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
    else:
        grade = percentage

    return grade
