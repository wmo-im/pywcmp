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

# abstract test for WCMP1 and WCMP2

from io import BytesIO

import click

from pywcmp.errors import TestSuiteError
from pywcmp.wcmp1.ats import WMOCoreMetadataProfileTestSuite13
from pywcmp.wcmp2.ats import WMOCoreMetadataProfileTestSuite2
from pywcmp.util import (get_cli_common_options, parse_wcmp, setup_logger,
                         urlopen_)


@click.group()
def ats():
    """abstract test suite"""
    pass


@click.command()
@click.pass_context
@get_cli_common_options
@click.argument('file_or_url')
def validate(ctx, file_or_url, logfile, verbosity):
    """validate against the abstract test suite"""

    setup_logger(verbosity, logfile)

    if file_or_url.startswith('http'):
        content = BytesIO(urlopen_(file_or_url).read())
    else:
        content = file_or_url

    click.echo(f'Validating {file_or_url}')

    try:
        data, wcmp_version_guess = parse_wcmp(content)
        if wcmp_version_guess == 1:
            cls = WMOCoreMetadataProfileTestSuite13
        elif wcmp_version_guess == 2:
            cls = WMOCoreMetadataProfileTestSuite2

        ts = cls(data)

        # run the tests
        try:
            ts.run_tests()
            click.echo('Success!')
        except TestSuiteError as err:
            msg = '\n'.join(err.errors)
            click.echo(msg)

    except ValueError as err:
        raise click.ClickException(err)


ats.add_command(validate)
