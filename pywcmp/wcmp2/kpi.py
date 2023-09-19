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

# WMO Core Metadata Profile Key Performance Indicators (KPIs)

import logging
import re

from bs4 import BeautifulSoup

from pywcmp.util import check_spelling

LOGGER = logging.getLogger(__name__)

# round percentages to x decimal places
ROUND = 3


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

        :returns: `tuple` of KPI name, achieved score, total score,
                  and comments
        """

        total = 0
        score = 0
        comments = []

        name = 'KPI: Good quality title'

        LOGGER.info(f'Running {name}')

        title = self.data['properties']['title']

        total = 8

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

        LOGGER.debug('Testing for title case')
        if title.istitle():
            score += 1
        else:
            comments.append('Title is not title case')

        LOGGER.debug('Testing for acronyms')
        if len(re.findall(r'([A-Z]\.*){2,}s?', title)) <= 3:
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

        return name, total, score, comments

    def kpi_description(self) -> tuple:
        """
        Implements KPI for Good quality description

        :returns: `tuple` of KPI name, achieved score, total score,
                  and comments
        """

        total = 0
        score = 0
        comments = []

        name = 'KPI: Good quality description'

        LOGGER.info(f'Running {name}')

        description = self.data['properties']['description']

        LOGGER.debug('Description is present')
        total += 4

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

        return name, total, score, comments

    def evaluate(self, kpi: str = None) -> dict:
        """
        Convenience function to run all tests

        :param kpi: `str` of KPI identifier

        :returns: `dict` of overall test report
        """

        known_kpis = [
            'kpi_title',
            'kpi_description'
        ]

        kpis_to_run = known_kpis

        if kpi is not None:
            selected_kpi = f'kpi_{kpi}'
            if selected_kpi not in known_kpis:
                msg = f'Invalid KPI number: {selected_kpi} is not in {known_kpis}'  # noqa
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
            overall_grade = calculate_grade(results['summary']['percentage'])
            results['summary']['grade'] = overall_grade

        return results


def generate_summary(results: dict) -> dict:
    """
    Generates a summary entry for given group of results

    :param results: results to generate the summary from

    :returns: `dict` of summary report
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

    return grade
