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
from dataclasses import dataclass, field
import logging
from pathlib import Path
from typing import Dict, List, Tuple

import click

from pywcmp.util import get_userdir

LOGGER = logging.getLogger(__name__)

topic_csvs = [
    'root',
    'version',
    'distribution',
    'country',
    'centre-id',
    'resource-type',
    'data-policy',
    'earth-system-domain'
]


@dataclass
class Topic:
    name: str
    description: str
    child: str


@dataclass
class TopicLevel:
    name: str
    topics: Dict[str, Topic] = field(default_factory=dict)


@dataclass
class TopicHierarchy:
    name: str = 'WIS 2.0 Topic Hierarchy'
    levels: List[TopicLevel] = field(default_factory=list)

    def __post_init__(self):
        dir_ = Path(get_userdir()) / 'wis2-topic-hierarchy'
        LOGGER.debug(f'Reading topic hierarchy files in {dir_}')
        for c in topic_csvs:
            filename = dir_ / f'{c}.csv'
            LOGGER.debug(f'Reading topic hierarchy file {filename}')
            level_name = filename.stem
            with filename.open() as fh:
                topics = {}
                reader = csv.DictReader(fh)
                for row in reader:
                    topic = Topic(row['Name'],
                                  row['Description'], row['Child'])

                    topics[row['Name']] = topic
                level = TopicLevel(level_name, topics)
                self.levels.append(level)

    def list_children(self, topic_hierarchy: str = None) -> Tuple[str, list]:
        """
        Lists children at a given level of a topic hierarchy

        :param topic_hierarchy: `str` of topic hierarchy

        :returns: tuple of level and its (`list` of) children
        """

        if topic_hierarchy is None:
            return '/', [level.name for level in self.levels]

        if not self.validate(topic_hierarchy):
            msg = 'Topic hierarchy is not valid'
            LOGGER.error(msg)
            raise ValueError(msg)

        step = len(topic_hierarchy.split('.'))

        return self.levels[step].name, list(self.levels[step].topics.keys())

    def validate(self, topic_hierarchy: str = None) -> bool:
        """
        Validates a topic hierarchy

        :param topic_hierarchy: `str` of topic hierarchy

        :returns: `bool` of whether topic hiearchy is valid
        """

        if topic_hierarchy is None:
            msg = 'Topic hierarchy is empty'
            LOGGER.error(msg)
            raise ValueError(msg)

        for step, topic in enumerate(topic_hierarchy.split('.')):
            level_name = self.levels[step].name

            LOGGER.debug(f'Validating step={step}, level={level_name}')

            if not topic:
                msg = f'Topic at step={step}, level={level_name} is empty'
                LOGGER.error(msg)
                return False

            if topic not in self.levels[step].topics:
                msg = (f'Topic {topic} at step={step}, level={level_name} '
                       f'not in {list(self.levels[step].topics.keys())}')
                LOGGER.error(msg)
                return False

        return True


@click.group()
def topics():
    """Topic hierarchy utilities"""
    pass


@click.command('list')
@click.pass_context
@click.option('--topic-hierarchy', '-th', help='Topic hierarchy')
def list_(ctx, topic_hierarchy):
    """List topic hierarchies at a given level"""

    th = TopicHierarchy()

    result = th.list_children(topic_hierarchy)
    click.echo(f'Level: {result[0]}')
    click.echo('Children:')
    for child in result[1]:
        click.echo(f'- {child}')


@click.command()
@click.pass_context
@click.option('--topic-hierarchy', '-th', help='Topic hierarchy')
def validate(ctx, topic_hierarchy):
    """Valite topic hierarchy"""

    th = TopicHierarchy()

    if th.validate(topic_hierarchy):
        click.echo('Valid')
    else:
        click.echo('Invalid')


topics.add_command(list_)
topics.add_command(validate)
