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
# Copyright (c) 2020 Government of Canada
# Copyright (c) 2020 IBL Software Engineering spol. s r. o.
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

import logging
import os
import ssl
import sys
from urllib.error import URLError
from urllib.request import urlopen

from lxml import etree

LOGGER = logging.getLogger(__name__)

NAMESPACES = {
    'gco': 'http://www.isotc211.org/2005/gco',
    'gmd': 'http://www.isotc211.org/2005/gmd',
    'gml': 'http://www.opengis.net/gml/3.2',
    'gmx': 'http://www.isotc211.org/2005/gmx',
    'xlink': 'http://www.w3.org/1999/xlink'
}


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


def get_codelists():
    """
    Helper function to assemble dict of WMO codelists

    :returns: `dict` of WMO codelists

    """
    codelists = {}
    userdir = get_userdir()
    xml = etree.parse('{}{}WMOCodeLists.xml'.format(userdir, os.sep))
    for cld in xml.xpath('gmx:codelistItem/gmx:CodeListDictionary', namespaces=NAMESPACES):
        identifier = cld.get(nspath_eval('gml:id'))
        codelists[identifier] = []
        for centry in cld.findall(nspath_eval('gmx:codeEntry/gmx:CodeDefinition/gml:identifier')):
            codelists[identifier].append(centry.text)
    return codelists


def get_string_or_anchor_values(element_tree, parent_xpath: str) -> list:
    """
    Returns list of strings (texts) from CharacterString or Anchor child elements of given Xpath

    :param element_tree : XML element tree (parsed document).
    :param parent_xpath : Path to the parent element of the CharacterString or Anchor.
    """
    values = []
    parent_elements = element_tree.findall(nspath_eval(parent_xpath))
    for parent in parent_elements:
        value_elements = parent.findall(nspath_eval('gco:CharacterString')) + parent.findall(nspath_eval('gmx:Anchor'))
        for element in value_elements:
            values.append(element.text)
    return values


def get_userdir() -> str:
    """
    Helper function to get userdir

    :returns: user's home directory
    """

    return '{}{}{}'.format(os.path.expanduser('~'), os.sep, '.pywcmp')


def nspath_eval(xpath: str) -> str:
    """
    Return an etree friendly xpath based expanding namespace
    into namespace URIs

    :param xpath: xpath string with namespace prefixes

    :returns: etree friendly xpath
    """

    out = []
    for chunks in xpath.split('/'):
        namespace, element = chunks.split(':')
        out.append('{{{}}}{}'.format(NAMESPACES[namespace], element))
    return '/'.join(out)


def setup_logger(loglevel: str = None, logfile: str = None):
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


def check_url(url: str, check_ssl: bool) -> dict:
    """
    Helper function to check link (URL) accessibility

    :param url: The URL to check
    :param check_ssl: Whether the SSL/TLS layer verification shall be made

    :returns: `dict` with details about the link
    """

    result = {}
    response = None
    result['url-original'] = url
    try:
        if check_ssl is False:
            LOGGER.debug('Creating unverified context')
            result['ssl'] = False
            context = ssl._create_unverified_context()
            response = urlopen(url, context=context)
        else:
            response = urlopen(url)
    except (ssl.SSLError, URLError) as err:
        LOGGER.debug(err)

    if response is None and check_ssl is True:
        return check_url(url, False)

    if response is not None:
        result['url-resolved'] = response.url
        if response.status > 300:
            LOGGER.debug('Request failed: {}'.format(response))
        result['accessible'] = response.status < 300
        if response.url.startswith("https") and check_ssl is True:
            result['ssl'] = True
    else:
        result['accessible'] = False
    return result


def validate_iso_xml(xml):
    """
    Perform XML Schema validation of ISO XML Metadata

    :param xml: file or string of XML

    :returns: `bool` of whether XML validates ISO schema
    """

    userdir = get_userdir()
    if not os.path.exists(userdir):
        raise IOError('{} does not exist'.format(userdir))
    if isinstance(xml, str):
        xml = etree.fromstring(xml)
    xsd = os.path.join(userdir, 'iso-all.xsd')
    LOGGER.debug('Validating {} against schema {}'.format(xml, xsd))
    schema = etree.XMLSchema(etree.parse(xsd))
    schema.assertValid(xml)
