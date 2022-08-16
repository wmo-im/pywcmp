# =================================================================
#
# Terms and Conditions of Use
#
# Unless otherwise noted, computer program source code of this
# distribution is covered under Crown Copyright, Government of
# Canada, and is distributed under the MIT License.
#
# The Canada wordmark and related graphics associated with this
# distribution are protected under trademark law and copyright law.
# No permission is granted to use them outside the parameters of
# the Government of Canada's corporate identity program. For
# more information, see
# http://www.tbs-sct.gc.ca/fip-pcim/index-eng.asp
#
# Copyright title to all 3rd party software distributed with this
# software is held by the respective copyright holders as noted in
# those files. Users are asked to read the 3rd Party Licenses
# referenced with those assets.
#
# Copyright (c) 2022 Government of Canada
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# =================================================================

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
