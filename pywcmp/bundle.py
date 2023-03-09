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

import io
import json
import logging
import os
import shutil
import zipfile

import click
from lxml import etree

from pywcmp.wcmp2.topics import build_topics, WIS2_TOPIC_HIERARCHY_LOOKUP
from pywcmp.util import get_cli_common_options, get_userdir, urlopen_, setup_logger

LOGGER = logging.getLogger(__name__)

USERDIR = get_userdir()

WCMP1_FILES = get_userdir() / 'wcmp-1.3'
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

    LOGGER.debug('Caching WCMP 1.3 artifacts')
    WCMP1_FILES.mkdir(parents=True, exist_ok=True)

    LOGGER.debug(f'Downloading WCMP1 schemas and codelists to {WCMP1_FILES}')  # noqa
    ZIPFILE_URL = 'https://wis.wmo.int/2011/schemata/iso19139_2007/19139.zip'  # noqa
    FH = io.BytesIO(urlopen_(ZIPFILE_URL).read())
    with zipfile.ZipFile(FH) as z:
        z.extractall(WCMP1_FILES)
    CODELIST_URL = 'https://wis.wmo.int/2012/codelists/WMOCodeLists.xml'

    schema_filename = WCMP1_FILES / 'WMOCodeLists.xml'

    with schema_filename.open('wb') as f:
        f.write(urlopen_(CODELIST_URL).read())

    # because some ISO instances ref both gmd and gmx, create a
    # stub xsd in order to validate
    SCHEMA = etree.Element('schema',
                           elementFormDefault='qualified',
                           version='1.0.0',
                           nsmap={
                               None: 'http://www.w3.org/2001/XMLSchema'
                           })

    schema_wrapper_filename = WCMP1_FILES / 'iso-all.xsd'

    with schema_wrapper_filename.open('wb') as f:
        for uri in ['gmd', 'gmx']:
            namespace = f'http://www.isotc211.org/2005/{uri}'
            schema_location = f'schema/{uri}/{uri}.xsd'

            etree.SubElement(SCHEMA, 'import',
                             namespace=namespace,
                             schemaLocation=schema_location)
        f.write(etree.tostring(SCHEMA, pretty_print=True))

    LOGGER.debug('Caching WCMP2 artifacts')
    LOGGER.debug(f'Downloading WCMP2 schema to {WCMP2_FILES}')
    WCMP2_FILES.mkdir(parents=True, exist_ok=True)
    WCMP2_SCHEMA = 'https://raw.githubusercontent.com/wmo-im/wcmp2/main/schemas/wcmp2-bundled.json'  # noqa

    json_schema = WCMP2_FILES / 'wcmp2-bundled.json'
    with json_schema.open('wb') as fh:
        fh.write(urlopen_(f'{WCMP2_SCHEMA}').read())

    LOGGER.debug('Downloading WIS2 topic hierarchy')
    WIS2_TOPIC_HIERARCHY_DIR.mkdir(parents=True, exist_ok=True)

    ZIPFILE_URL = 'https://github.com/wmo-im/wis2-topic-hierarchy/archive/refs/heads/main.zip'  # noqa
    FH = io.BytesIO(urlopen_(ZIPFILE_URL).read())
    with zipfile.ZipFile(FH) as z:
        LOGGER.debug(f'Processing zipfile "{z.filename}"')
        for name in z.namelist():
            LOGGER.debug(f'Processing entry "{name}"')
            if 'wis2-topic-hierarchy-main/topic-hierarchy' in name:
                filename = os.path.basename(name)

                if not filename:
                    continue

                dest_file = WIS2_TOPIC_HIERARCHY_DIR / filename
                LOGGER.debug(f'Creating "{dest_file}"')
                with z.open(name) as src, dest_file.open('wb') as dest:
                    shutil.copyfileobj(src, dest)

    with WIS2_TOPIC_HIERARCHY_LOOKUP.open('w') as fh:
        content = build_topics()
        fh.write(json.dumps(content, indent=4))


bundle.add_command(sync)
