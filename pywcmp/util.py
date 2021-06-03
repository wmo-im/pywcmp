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
# Copyright (c) 2020-2021 Government of Canada
# Copyright (c) 2020-2021 IBL Software Engineering spol. s r. o.
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
from datetime import datetime, timezone, timedelta
from dateutil.parser import parse
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
    Helper function to assemble dict of ISO and WMO codelists

    :param authority: code list authority (iso or wmo)

    :returns: `dict` of ISO and WMO codelists

    """

    codelists = {}
    userdir = get_userdir()

    codelist_files = {
        'iso': f'{userdir}/schema/resources/Codelist/gmxCodelists.xml',
        'wmo': f'{userdir}{os.sep}WMOCodeLists.xml'
    }

    for key, value in codelist_files.items():
        codelists[key] = {}
        xml = etree.parse(value)
        for cld in xml.xpath('gmx:codelistItem/gmx:CodeListDictionary', namespaces=NAMESPACES):
            identifier = cld.get(nspath_eval('gml:id'))
            codelists[key][identifier] = []
            for centry in cld.findall(nspath_eval('gmx:codeEntry/gmx:CodeDefinition/gml:identifier')):
                codelists[key][identifier].append(centry.text)

    return codelists


def get_string_or_anchor_value(parent) -> list:
    """
    Returns list of strings (texts) from CharacterString or Anchor child elements of the given element

    :param parent : The element to check
    """
    values = []
    value_elements = parent.findall(nspath_eval('gco:CharacterString')) + parent.findall(nspath_eval('gmx:Anchor'))
    for element in value_elements:
        values.append(element.text)
    return values


def get_string_or_anchor_values(parent_elements: list) -> list:
    """
    Returns list of strings (texts) from CharacterString or Anchor child elements of given parent_elements

    :param parent_elements : List of parent elements of the CharacterString or Anchor to read.
    """
    values = []
    for parent in parent_elements:
        values += get_string_or_anchor_value(parent)
    return values


def get_keyword_info(main_keyword_element) -> tuple:
    """
    Returns tuple with keywords, type value(s) and thesaurus(es) for given "MD_Keywords" element

    :param main_keyword_element : The element to check
    """

    keywords = main_keyword_element.findall(nspath_eval('gmd:keyword'))
    type_element = get_codelist_values(main_keyword_element.findall(nspath_eval('gmd:type/gmd:MD_KeywordTypeCode')))
    thesauruses = main_keyword_element.findall(nspath_eval('gmd:thesaurusName/gmd:CI_Citation/gmd:title'))
    return keywords, type_element, thesauruses


def get_codelist_values(elements: list) -> list:
    """
    Returns list of code list values as strings for all elements (except the ones with no value)
    The value can be in the element attribute or text node.

    :param elements : The elements to check
    """
    values = []
    for element in elements:
        value = element.get('codeListValue')
        if value is None:
            value = element.text
        if value is not None:
            values.append(value)
    return values


def parse_time_position(element) -> datetime:
    """
    Returns datetime extracted from the given GML element or None if parsing failed.
    The parsing is rather benevolent here to allow mixing of "Zulu" and "naive" time strings (and other oddities),
    in the hope that all meteorological data refer to UTC.

    :param element : XML / GML element (e.g. gml:beginPosition)
    """
    indeterminate_pos = element.get('indeterminatePosition')
    if indeterminate_pos is not None:
        if indeterminate_pos in ["now", "unknown"]:
            return datetime.now(timezone.utc)
        elif indeterminate_pos == "before":
            return datetime.now(timezone.utc) - timedelta(hours=24)
        elif indeterminate_pos == "after":
            return datetime.now(timezone.utc) + timedelta(hours=24)
        else:
            LOGGER.debug(f'Time point has unexpected value of indeterminatePosition: {indeterminate_pos}')
    elif element.text is not None:
        text_to_parse = element.text
        if text_to_parse.endswith('Z'):
            text_to_parse = text_to_parse[0:-1]
        dtg = parse(text_to_parse, fuzzy=True, ignoretz=True).replace(tzinfo=timezone.utc)
        return dtg
    return None


def get_userdir() -> str:
    """
    Helper function to get userdir

    :returns: user's home directory
    """

    return f'{os.path.expanduser("~")}{os.sep}.pywcmp'


def nspath_eval(xpath: str) -> str:
    """
    Return an etree friendly xpath based expanding namespace
    into namespace URIs

    :param xpath: xpath string with namespace prefixes

    :returns: etree friendly xpath
    """

    out = []
    for chunk in xpath.split('/'):
        if ':' in chunk:
            namespace, element = chunk.split(':')
            out.append(f'{{{NAMESPACES[namespace]}}}{element}')
        else:
            out.append(chunk)
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

    response = None
    result = {
        'mime-type': None,
        'url-original': url
    }

    try:
        if check_ssl is False:
            LOGGER.debug('Creating unverified context')
            result['ssl'] = False
            context = ssl._create_unverified_context()
            response = urlopen(url, context=context)
        else:
            response = urlopen(url)
    except (ssl.SSLError, URLError, ValueError) as err:
        LOGGER.debug(err)

    if response is None and check_ssl is True:
        return check_url(url, False)

    if response is not None:
        result['url-resolved'] = response.url
        if response.status > 300:
            LOGGER.debug(f'Request failed: {response}')
        result['accessible'] = response.status < 300
        result['mime-type'] = response.headers.get_content_type()
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
        raise IOError(f'{userdir} does not exist')
    if isinstance(xml, str):
        xml = etree.fromstring(xml)
    xsd = os.path.join(userdir, 'iso-all.xsd')
    LOGGER.debug(f'Validating {xml} against schema {xsd}')
    schema = etree.XMLSchema(etree.parse(xsd))
    schema.assertValid(xml)


def parse_wcmp(content):
    """
    Parse a buffer into an etree ElementTree

    :param content: str of xml content

    :returns: `lxml.etree._ElementTree` object of WCMP
    """

    try:
        exml = etree.parse(content)
    except etree.XMLSyntaxError as err:
        LOGGER.error(err)
        raise RuntimeError('Syntax error')

    root_tag = exml.getroot().tag

    if root_tag != '{http://www.isotc211.org/2005/gmd}MD_Metadata':
        raise RuntimeError('Does not look like a WCMP document!')

    return exml
