###############################################################################
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#          Ján Osuský <jan.osusky@iblsoft.com>
#
# Copyright (c) 2024 Tom Kralidis
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

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import ssl
import sys
from urllib.error import URLError
from urllib.request import urlopen
from urllib.parse import urlparse

from spellchecker import SpellChecker

LOGGER = logging.getLogger(__name__)
THISDIR = Path(__file__).parent.resolve()


def check_spelling(text: str) -> list:
    """
    Helper function to spell check a string

    :returns: `list` of unknown / misspelled words
    """

    LOGGER.debug(f'Spellchecking {text}')
    spell = SpellChecker()

    dictionary = THISDIR / 'dictionary.txt'
    LOGGER.debug(f'Loading custom dictionary {dictionary}')
    spell.word_frequency.load_text_file(f'{dictionary}')

    return list(spell.unknown(spell.split_words(text)))


def get_cli_common_options(function):
    """
    Define common CLI options
    """

    import click
    function = click.option('--verbosity', '-v',
                            type=click.Choice(
                                ['ERROR', 'WARNING', 'INFO', 'DEBUG']),
                            help='Verbosity')(function)
    function = click.option('--log', '-l', 'logfile',
                            type=click.Path(writable=True, dir_okay=False),
                            help='Log file')(function)
    return function


def get_userdir() -> str:
    """
    Helper function to get userdir

    :returns: user's home directory
    """

    return Path.home() / '.pywcmp'


def setup_logger(loglevel: str = None, logfile: str = None) -> None:
    """
    Setup logging

    :param loglevel: logging level
    :param logfile: logfile location

    :returns: void (creates logging instance)
    """

    if loglevel is None and logfile is None:  # no logging
        return

    if loglevel is None and logfile is not None:
        loglevel = 'INFO'

    log_format = \
        '[%(asctime)s] %(levelname)s - %(message)s'
    date_format = '%Y-%m-%dT%H:%M:%SZ'

    loglevels = {
        'CRITICAL': logging.CRITICAL,
        'ERROR': logging.ERROR,
        'WARNING': logging.WARNING,
        'INFO': logging.INFO,
        'DEBUG': logging.DEBUG,
        'NOTSET': logging.NOTSET,
    }

    loglevel = loglevels[loglevel]

    if logfile is not None:  # log to file
        logging.basicConfig(level=loglevel, datefmt=date_format,
                            format=log_format, filename=logfile)
    elif loglevel is not None:  # log to stdout
        logging.basicConfig(level=loglevel, datefmt=date_format,
                            format=log_format, stream=sys.stdout)
        LOGGER.debug('Logging initialized')


def urlopen_(url: str):
    """
    Helper function for downloading a URL

    :param url: URL to download

    :returns: `http.client.HTTPResponse`
    """

    try:
        response = urlopen(url)
    except (ssl.SSLError, URLError) as err:
        LOGGER.warning(err)
        LOGGER.warning('Creating unverified context')
        context = ssl._create_unverified_context()

        response = urlopen(url, context=context)

    return response


def check_url(url: str, check_ssl: bool, timeout: int = 30) -> dict:
    """
    Helper function to check link (URL) accessibility

    :param url: The URL to check
    :param check_ssl: Whether the SSL/TLS layer verification shall be made
    :param timeout: timeout, in seconds (default: 30)

    :returns: `dict` with details about the link
    """

    response = None
    result = {
        'mime-type': None,
        'url-original': url
    }

    try:
        if not check_ssl:
            LOGGER.debug('Creating unverified context')
            result['ssl'] = False
            context = ssl._create_unverified_context()
            response = urlopen(url, context=context, timeout=timeout)
        else:
            response = urlopen(url, timeout=timeout)
    except TimeoutError as err:
        LOGGER.debug(f'Timeout error: {err}')
    except (ssl.SSLError, URLError, ValueError) as err:
        LOGGER.debug(f'SSL/URL error: {err}')
        LOGGER.debug(err)
    except Exception as err:
        LOGGER.debug(f'Other error: {err}')
        LOGGER.debug(err)

    if response is None and check_ssl:
        return check_url(url, False)

    if response is not None:
        result['url-resolved'] = response.url
        parsed_uri = urlparse(response.url)
        if parsed_uri.scheme in ('http', 'https'):
            if response.status > 300:
                LOGGER.debug(f'Request failed: {response}')
            result['accessible'] = response.status < 300
            result['mime-type'] = response.headers.get_content_type()
        else:
            result['accessible'] = True
        if parsed_uri.scheme in ('https') and check_ssl:
            result['ssl'] = True
    else:
        result['accessible'] = False
    return result


def parse_wcmp(content: str) -> dict:
    """
    Parse a string of WCMP into a JSON dict (WCMP2)

    :param content: `str` of JSON

    :returns: `dict` object of WCMP
    """

    LOGGER.debug('Attempting to parse as JSON')
    try:
        data = json.loads(content)
    except json.decoder.JSONDecodeError as err:
        LOGGER.error(err)
        raise RuntimeError(f'Encoding error: {err}')

    return data


def get_current_datetime_rfc3339() -> str:
    """
    Gets the current datetime in RFC3339 format

    :returns: `str` of RFC3339
    """

    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def is_valid_created_datetime(value: str) -> bool:
    """
    Helper function to test for accepted RFC3339 strings

    :param value: `str` of datetime

    :returns: `bool` of whether datetime is valid/acceptable
    """

    datetime_formats = [
        '%Y-%m-%dT%H:%M:%SZ',     # 2024-08-09T14:29Z
        '%Y-%m-%dT%H:%M:%S.%fZ',  # 2024-08-09T14:29.12Z
        '%Y-%m-%dT%H:%M:%S%z'     # 2024-08-09T14:29+0400
    ]

    for datetime_format in datetime_formats:
        try:
            datetime.strptime(value, datetime_format)
            return True
        except ValueError as err:
            msg = f'datetime {value} invalid against {datetime_format}: {err}'
            LOGGER.debug(msg)

    return False
