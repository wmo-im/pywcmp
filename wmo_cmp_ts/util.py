# -*- coding: ISO-8859-15 -*-

import logging
import os
import tempfile
from lxml import etree

LOGGER = logging.getLogger(__name__)


def get_tempdir():
    """Helper function to get tempdir"""
    return '%s%s%s' % (tempfile.gettempdir(), os.sep, 'wmo-cmp-ts')


def nspath_eval(xpath, nsmap):
    """Return an etree friendly xpath"""
    out = []
    for chunks in xpath.split('/'):
        namespace, element = chunks.split(':')
        out.append('{%s}%s' % (nsmap[namespace], element))
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
