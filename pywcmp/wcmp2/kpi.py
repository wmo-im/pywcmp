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

# WMO Core Metadata Profile Key Performance Indicators (KPIs)

import logging

LOGGER = logging.getLogger(__name__)

# round percentages to x decimal places
ROUND = 3


class WMOCoreMetadataProfileKeyPerformanceIndicators:
    """Key Performance Indicators for WMO Core Metadata Profile"""

    def __init__(self, data):
        """
        initializer

        :param data: dict of WCMP JSON

        :returns: `pywcmp.wcmp2.kpi.WMOCoreMetadataProfileKeyPerformanceIndicators`
        """

        self.data = data
        self.codelists = None

    def kpi_xxx(self) -> tuple:
        """
        Implements KPI-XXX: TODO

        :returns: `tuple` of KPI name, achieved score, total score, and comments
        """

        name = 'KPI-xxx: TODO'

        LOGGER.info(f'Running {name}')

        total = 10
        comments = []

        return 'kpi_001', total, 10, comments


def group_kpi_results(kpis_results: dict) -> dict:
    """
    Groups KPI results by category

    :param kpis_results: `dict` of the results to be grouped
    """

    return {}
