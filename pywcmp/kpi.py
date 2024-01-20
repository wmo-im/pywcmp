###############################################################################
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#          Ján Osuský <jan.osusky@iblsoft.com>
#
# Copyright (c) 2023 Tom Kralidis
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

import json
import logging

import click

from pywcmp.ets import WMOCoreMetadataProfileTestSuite2
from pywcmp.wcmp2.kpi import (
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
@click.option('--fail-on-ets/--no-fail-on-ets',
              '-f', default=True, help='Stop the KPI on failing ETS')
@click.option('--summary', '-s', is_flag=True, default=False,
              help='Provide summary of KPI test results')
@click.option('--kpi', '-k', help='KPI to run, default is all')
def validate(ctx, file_or_url, summary, kpi, logfile, verbosity,
             fail_on_ets=True):
    """run key performance indicators"""

    setup_logger(verbosity, logfile)

    if file_or_url.startswith('http'):
        content = urlopen_(file_or_url).read()
    else:
        with open(file_or_url) as fh:
            content = fh.read()

    click.echo(f'Validating {file_or_url}')

    try:
        data = parse_wcmp(content)
    except Exception as err:
        raise click.ClickException(err)
        ctx.exit(1)

    if fail_on_ets:
        ts = WMOCoreMetadataProfileTestSuite2(data)
        try:
            _ = ts.run_tests(fail_on_schema_validation=True)
        except Exception as err:
            raise click.ClickException(err)
            ctx.exit(1)

    kpis = wcmp_kpis2(data)

    try:
        kpis_results = kpis.evaluate(kpi)
    except ValueError as err:
        raise click.UsageError(f'Invalid KPI {kpi}: {err}')
        ctx.exit(1)

    if not summary or kpi is not None:
        click.echo(json.dumps(kpis_results, indent=4))
    else:
        click.echo(json.dumps(kpis_results['summary'], indent=4))


kpi.add_command(validate)
