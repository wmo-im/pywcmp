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

import io
import logging
import os
import shutil
import zipfile

import click

from pywcmp.util import (get_cli_common_options, get_userdir, urlopen_,
                         setup_logger)

LOGGER = logging.getLogger(__name__)

USERDIR = get_userdir()

WCMP2_FILES = get_userdir() / 'wcmp-2'
WIS2_TOPIC_HIERARCHY_DIR = get_userdir() / 'wis2-topic-hierarchy'


@click.group()
def bundle():
    """Configuration bundle management"""
    pass


@click.command()
@get_cli_common_options
@click.pass_context
def sync(ctx, logfile, verbosity):
    "Sync configuration bundle"""

    setup_logger(verbosity, logfile)
    LOGGER.debug('Caching schemas, codelists and topic hierarchy')

    if USERDIR.exists():
        shutil.rmtree(USERDIR)

    LOGGER.debug('Caching WCMP2 artifacts')
    LOGGER.debug(f'Downloading WCMP2 schema to {WCMP2_FILES}')
    WCMP2_FILES.mkdir(parents=True, exist_ok=True)
    WCMP2_SCHEMA = 'https://raw.githubusercontent.com/wmo-im/wcmp2/main/schemas/wcmp2-bundled.json'  # noqa

    json_schema = WCMP2_FILES / 'wcmp2-bundled.json'
    with json_schema.open('wb') as fh:
        fh.write(urlopen_(f'{WCMP2_SCHEMA}').read())

    WCMP2_CODELISTS = WCMP2_FILES / 'codelists'
    LOGGER.debug(f'Downloading WCMP2 codelists to {WCMP2_CODELISTS}')
    WCMP2_CODELISTS.mkdir(parents=True, exist_ok=True)
    CODELISTS_URL = 'https://github.com/wmo-im/wcmp2-codelists/archive/refs/heads/main.zip'  # noqa
    FH = io.BytesIO(urlopen_(CODELISTS_URL).read())
    with zipfile.ZipFile(FH) as z:
        LOGGER.debug(f'Processing zipfile "{z.filename}"')
        for name in z.namelist():
            LOGGER.debug(f'Processing entry "{name}"')
            if '.csv' in name:
                filename = os.path.basename(name)

                if not filename:
                    continue

                dest_file = WCMP2_CODELISTS / filename
                LOGGER.debug(f'Creating "{dest_file}"')
                with z.open(name) as src, dest_file.open('wb') as dest:
                    shutil.copyfileobj(src, dest)

    LOGGER.debug('Downloading WIS2 topic hierarchy')
    WIS2_TOPIC_HIERARCHY_DIR.mkdir(parents=True, exist_ok=True)

    ZIPFILE_URL = 'https://wmo-im.github.io/wis2-topic-hierarchy/wth-bundle.zip'  # noqa
    FH = io.BytesIO(urlopen_(ZIPFILE_URL).read())
    with zipfile.ZipFile(FH) as z:
        LOGGER.debug(f'Processing zipfile "{z.filename}"')
        for name in z.namelist():
            LOGGER.debug(f'Processing entry "{name}"')
            filename = os.path.basename(name)

            dest_file = WIS2_TOPIC_HIERARCHY_DIR / filename
            LOGGER.debug(f'Creating "{dest_file}"')
            with z.open(name) as src, dest_file.open('wb') as dest:
                shutil.copyfileobj(src, dest)

    LOGGER.debug('Downloading IANA link relations')
    IANA_URL = 'https://www.iana.org/assignments/link-relations/link-relations-1.csv'  # noqa
    iana_file = WCMP2_FILES / 'link-relations-1.csv'
    with iana_file.open('wb') as fh:
        fh.write(urlopen_(f'{IANA_URL}').read())


bundle.add_command(sync)
