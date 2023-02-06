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

import logging
import os
from datetime import datetime, timezone, timedelta
from dateutil.parser import parse

from lxml import etree

from pywcmp.util import get_userdir

LOGGER = logging.getLogger(__name__)

NAMESPACES = {
    'gco': 'http://www.isotc211.org/2005/gco',
    'gmd': 'http://www.isotc211.org/2005/gmd',
    'gml': 'http://www.opengis.net/gml/3.2',
    'gmx': 'http://www.isotc211.org/2005/gmx',
    'xlink': 'http://www.w3.org/1999/xlink'
}


def get_codelists():
    """
    Helper function to assemble dict of ISO and WMO codelists

    :param authority: code list authority (iso or wmo)

    :returns: `dict` of ISO and WMO codelists

    """

    codelists = {}
    userdir = get_userdir()

    codelist_files = {
        'iso': f'{userdir}/wcmp-1.3/schema/resources/Codelist/gmxCodelists.xml',
        'wmo': f'{userdir}/wcmp-1.3/WMOCodeLists.xml'
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

        try:
            dtg = parse(text_to_parse, fuzzy=True, ignoretz=True).replace(tzinfo=timezone.utc)
            return dtg
        except Exception as err:
            msg = f'Invalid time string: {err}'
            LOGGER.debug(msg)

    return None


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
    xsd = os.path.join(userdir, 'wcmp-1.3', 'iso-all.xsd')
    LOGGER.debug(f'Validating {xml} against schema {xsd}')
    schema = etree.XMLSchema(etree.parse(xsd))
    schema.assertValid(xml)
