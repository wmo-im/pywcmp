# -*- coding: utf-8 -*-
# =================================================================
#
# Terms and Conditions of Use
#
# Unless otherwise noted, computer program source code of this
# distribution # is covered under Crown Copyright, Government of
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
# Copyright (c) 2016 Government of Canada
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
from lxml import etree

LOGGER = logging.getLogger(__name__)

NAMESPACES = {
    'gco': 'http://www.isotc211.org/2005/gco',
    'gmd': 'http://www.isotc211.org/2005/gmd',
    'gml': 'http://www.opengis.net/gml/3.2',
    'gmx': 'http://www.isotc211.org/2005/gmx',
    'xlink': 'http://www.w3.org/1999/xlink',
}


def get_codelists():
    """Helper function to assemble dict of WMO codelists"""
    codelists = {}
    userdir = get_userdir()
    xml = etree.parse('%s%sWMOCodeLists.xml' % (userdir, os.sep))
    for cld in xml.xpath('gmx:codelistItem/gmx:CodeListDictionary', namespaces=NAMESPACES):
        identifier = cld.get(nspath_eval('gml:id'))
        codelists[identifier] = []
        for centry in cld.findall(nspath_eval('gmx:codeEntry/gmx:CodeDefinition/gml:identifier')):
            codelists[identifier].append(centry.text)
    return codelists


def get_userdir():
    """Helper function to get userdir"""
    return '%s%s%s' % (os.path.expanduser('~'), os.sep, '.wmo-cmp-ts')


def nspath_eval(xpath):
    """Return an etree friendly xpath"""
    out = []
    for chunks in xpath.split('/'):
        namespace, element = chunks.split(':')
        out.append('{%s}%s' % (NAMESPACES[namespace], element))
    return '/'.join(out)


def validate_iso_xml(xml):
    """Perform XML Schema validation of ISO XML Metadata"""
    userdir = get_userdir()
    if not os.path.exists(userdir):
        raise IOError('%s does not exist' % userdir)
    if isinstance(xml, str):
        xml = etree.fromstring(xml)
    xsd = os.path.join(userdir, 'iso-all.xsd')
    LOGGER.info('Validating %s against schema %s', xml, xsd)
    schema = etree.XMLSchema(etree.parse(xsd))
    schema.assertValid(xml)
