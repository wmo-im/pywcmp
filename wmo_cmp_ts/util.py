# -*- coding: ISO-8859-15 -*-

import logging
import os
import tempfile
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
    tempdir = get_tempdir()
    xml = etree.parse('%s%sWMOCodeLists.xml' % (tempdir, os.sep))
    for cld in xml.xpath('gmx:codelistItem/gmx:CodeListDictionary', namespaces=NAMESPACES):
        identifier = cld.get(nspath_eval('gml:id'))
        codelists[identifier] = []
        for centry in cld.findall(nspath_eval('gmx:codeEntry/gmx:CodeDefinition/gml:identifier')):
            codelists[identifier].append(centry.text)
    return codelists


def get_tempdir():
    """Helper function to get tempdir"""
    return '%s%s%s' % (tempfile.gettempdir(), os.sep, 'wmo-cmp-ts')


def nspath_eval(xpath):
    """Return an etree friendly xpath"""
    out = []
    for chunks in xpath.split('/'):
        namespace, element = chunks.split(':')
        out.append('{%s}%s' % (NAMESPACES[namespace], element))
    return '/'.join(out)


def validate_iso_xml(xml):
    """Perform XML Schema validation of ISO XML Metadata"""
    tempdir = get_tempdir()
    if not os.path.exists(tempdir):
        raise IOError('%s does not exist' % tempdir)
    if isinstance(xml, str):
        xml = etree.fromstring(xml)
    xsd = os.path.join(tempdir, 'iso-all.xsd')
    LOGGER.info('Validating %s against schema %s', xml, xsd)
    schema = etree.XMLSchema(etree.parse(xsd))
    schema.assertValid(xml)
