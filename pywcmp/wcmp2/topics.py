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

import csv
import json
import logging
from pathlib import Path
from typing import Dict, List

import click

from pywcmp.util import get_cli_common_options, get_userdir, setup_logger

LOGGER = logging.getLogger(__name__)


WIS2_TOPIC_HIERARCHY_LOOKUP = Path(get_userdir()) / 'wis2-topic-hierarchy' / 'all.json'  # noqa


def rstrip_add(value: str, token: str = '/', pad_again: bool = False):
    """
    Strips and adds trailing string

    :param value: `str` of value
    :param token: `str` of token to rstrip and add
    :param pad_again: `bool` of whether to right pad the string witht token

    :returns: string of rstrip'd and added value
    """

    value2 = value

    if value2.endswith(token):
        value2 = value2[:-1]

    if pad_again:
        value2 = f'{value2}{token}'

    return value2


def build_topics() -> Dict[str, list]:
    """
    Builds bundled/dereferenced dict or topic list

    :returns: `dict` of list of topics
    """

    content = {
        'topics': []
    }

    root_topic = 'channel'
    dir_ = Path(get_userdir()) / 'wis2-topic-hierarchy'
    LOGGER.debug(f'Topic hierarchy files location: {dir_}')

    def process_level(level, parent=None):
        level_file = dir_ / f'{level}.csv'
        if level_file.exists():
            with level_file.open() as fh:
                LOGGER.debug(f'Reading topic hierarchy file {level_file}')
                reader = csv.DictReader(fh)

                for row in reader:
                    if parent is not None:
                        path = f"{parent}/{row['Name']}"
                    else:
                        path = row['Name']

                    content['topics'].append(path)
                    process_level(row['Child'], path)

        else:
            LOGGER.warning(f'Topic file {level_file} does not exist')

    root_file = dir_ / f'{root_topic}.csv'
    process_level(root_file.stem)

    return content


class TopicHierarchy:
    def __init__(self):
        with WIS2_TOPIC_HIERARCHY_LOOKUP.open() as fh:
            self.topics = json.load(fh)['topics']

    def list_children(self, topic_hierarchy: str = None) -> List[str]:
        """
        Lists children at a given level of a topic hierarchy

        :param topic_hierarchy: `str` of topic hierarchy

        :returns: `list` of topic children
        """

        matches = []

        if topic_hierarchy is None:
            LOGGER.debug('Dumping root topic children')
            matches = list(set([i.split('/')[0] for i in self.topics]))
            return matches

        th = rstrip_add(topic_hierarchy)

        if not self.validate(th):
            msg = 'Invalid topic'
            LOGGER.info(msg)
            raise ValueError(msg)

        th = rstrip_add(topic_hierarchy, pad_again=True)

        for topic in self.topics:
            topic2 = rstrip_add(topic, pad_again=True)
            if topic2.startswith(th):
                child = topic2.replace(th, '').split('/')[0]
                if child:
                    matches.append(child)

        if not matches:
            msg = f'No matching topics for {topic_hierarchy}'
            LOGGER.info(msg)
            raise ValueError(msg)

        return list(set(matches))

    def validate(self, topic_hierarchy: str = None,
                 fuzzy: str = False) -> bool:
        """
        Validates a topic hierarchy

        :param topic_hierarchy: `str` of topic hierarchy
        :param fuzzy: `bool` of whether to apply fuzzy logic

        :returns: `bool` of whether topic hierarchy is valid
        """

        LOGGER.debug(f'Validating topic hierarchy {topic_hierarchy}')

        if topic_hierarchy is None:
            msg = 'Topic hierarchy is empty'
            LOGGER.info(msg)
            raise ValueError(msg)

        if fuzzy:
            LOGGER.debug('Applying fuzzy logic')
            if [t for t in self.topics if topic_hierarchy in t]:
                return True
            else:
                return False
        else:
            return topic_hierarchy in self.topics


@click.group()
def topics():
    """Topic hierarchy utilities"""
    pass


@click.command('list')
@click.pass_context
@get_cli_common_options
@click.argument('topic-hierarchy')
def list_(ctx, topic_hierarchy, logfile, verbosity):
    """List topic hierarchies at a given level"""

    setup_logger(verbosity, logfile)

    th = TopicHierarchy()

    try:
        matching_topics = th.list_children(topic_hierarchy)
        click.echo('Matching topics')
        for matching_topic in matching_topics:
            click.echo(f'- {matching_topic}')
    except ValueError as err:
        raise click.ClickException(err)


@click.command()
@click.pass_context
@get_cli_common_options
@click.argument('topic-hierarchy')
@click.option('--fuzzy', '-f', is_flag=True, help='Apply fuzzy search',
              default=False)
def validate(ctx, topic_hierarchy, fuzzy, logfile, verbosity):
    """Valite topic hierarchy"""

    setup_logger(verbosity, logfile)

    th = TopicHierarchy()

    if th.validate(topic_hierarchy, fuzzy):
        click.echo('Valid')
    else:
        click.echo('Invalid')


topics.add_command(list_)
topics.add_command(validate)
