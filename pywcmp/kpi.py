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

from io import BytesIO
import json
import logging

import click

from pywcmp.wcmp1.kpi import (
    group_kpi_results as group_kpi_results1,
    WMOCoreMetadataProfileKeyPerformanceIndicators as wcmp_kpis1
)
from pywcmp.wcmp2.kpi import (
    group_kpi_results as group_kpi_results2,
    WMOCoreMetadataProfileKeyPerformanceIndicators as wcmp_kpis2
)
from pywcmp.util import (get_cli_common_options, parse_wcmp, setup_logger,
                         urlopen_)

LOGGER = logging.getLogger(__name__)


@click.group()
def kpi():
    """key performance indicators"""
    pass


@click.command()
@click.pass_context
@get_cli_common_options
@click.argument('file_or_url')
@click.option('--summary', '-s', is_flag=True, default=False,
              help='Provide summary of KPI test results')
@click.option('--group', '-g', is_flag=True, default=False,
              help='Group KPIs by into categories')
@click.option('--kpi', '-k', default=0, help='KPI to run, default is all')
def validate(ctx, file_or_url, summary, group, kpi, logfile, verbosity):
    """run key performance indicators"""

    setup_logger(verbosity, logfile)

    if file_or_url.startswith('http'):
        content = BytesIO(urlopen_(file_or_url).read())
    else:
        content = file_or_url

    click.echo(f'Validating {file_or_url}')

    try:
        data, wcmp_version_guess = parse_wcmp(content)
    except Exception as err:
        raise click.ClickException(err)

    if wcmp_version_guess == 1:
        cls = wcmp_kpis1
        group_kpi_results = group_kpi_results1
    elif wcmp_version_guess == 2:
        cls = wcmp_kpis2
        group_kpi_results = group_kpi_results2

    kpis = cls(data)

    try:
        kpis_results = kpis.evaluate(kpi)
    except ValueError as err:
        raise click.UsageError(f'Invalid KPI {kpi}: {err}')

    if group and kpi == 0:
        kpis_results = group_kpi_results(kpis_results)

    if not summary or kpi != 0:
        click.echo(json.dumps(kpis_results, indent=4))
    else:
        click.echo(json.dumps(kpis_results['summary'], indent=4))


kpi.add_command(validate)
