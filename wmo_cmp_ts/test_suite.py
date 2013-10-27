# -*- coding: ISO-8859-15 -*-

import logging
from wmo_cmp_ts.util import nspath_eval, validate_iso_xml

LOGGER = logging.getLogger(__name__)

CODELIST_PREFIX = 'http://wis.wmo.int/2012/codelists/WMOCodeLists.xml'

NAMESPACES = {
    'gmd': 'http://www.isotc211.org/2005/gmd',
    'gml': 'http://www.opengis.net/gml/3.2',
    'gmx': 'http://www.isotc211.org/2005/gmx',
    'xlink': 'http://www.w3.org/1999/xlink',
}


def msg(testid, test_description):
    """Convenience function to print test props"""
    requirement = testid.split('test_requirement_')[-1].replace('_', '.')
    return 'Requirement %s:\n    %s' % (requirement, test_description)


def gen_test_id(tid):
    """Convenience function to print Test id"""
    return 'http://wis.wmo.int/2012/metadata/conf/%s' % tid


class WMOCoreMetadataProfileTestSuite13(object):
    """Test suite for WMO Core Metadata Profile assertions"""

    def __init__(self, exml):
        """init"""
        self.test_id = None
        self.exml = exml  # serialized already
        self.namespaces = self.exml.getroot().nsmap

    def test_requirement_6_1_1(self):
        """Each WIS Discovery Metadata record shall validate without error against the XML schemas defined in ISO/TS 19139:2007."""
        self.test_id = gen_test_id('ISO-TS-19139-2007-xml-schema-validation')
        validate_iso_xml(self.exml)

    def test_requirement_6_1_2(self):
        """Each WIS Discovery Metadata record shall validate without error against the rule-based constraints listed in ISO/TS 19139:2007 Annex A (Table A.1)."""
        self.test_id = gen_test_id('ISO-TS-19139-2007-rule-based-validation')

    def test_requirement_6_2_1(self):
        """Each WIS Discovery Metadata record shall explicitly name all namespaces used within the record; use of default namespaces is prohibited."""
        self.test_id = gen_test_id('explicit-xml-namespace-identification')

        assert(None not in self.namespaces), self.test_requirement_6_2_1.__doc__

    def test_requirement_6_3_1(self):
        """Each WIS Discovery Metadata record shall declare the following XML namespace for GML: http://www.opengis.net/gml/3.2."""
        self.test_id = gen_test_id('gml-namespace-specification')

        if 'gml' in self.namespaces:
            assert(self.namespaces['gml'] == NAMESPACES['gml']), self.test_requirement_6_3_1.__doc__

    def test_requirement_8_1_1(self):
        """Each WIS Discovery Metadata record shall include one gmd:MD_Metadata/gmd:fileIdentifier attribute."""
        self.test_id = gen_test_id('fileIdentifier-cardinality')

        ids = self.exml.findall(nspath_eval('gmd:fileIdentifier', NAMESPACES))
        assert(len(ids) == 1), self.test_requirement_8_1_1.__doc__

    def test_requirement_8_2_1(self):
        """Each WIS Discovery Metadata record shall include at least one keyword from the WMO_CategoryCode code list."""
        self.test_id = gen_test_id('WMO_CategoryCode-keyword-cardinality')

        # (i) check thesaurus
        node = self.exml.xpath('/gmd:MD_Metadata/gmd:identificationInfo//gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:thesaurusName/gmd:CI_Citation/gmd:title', namespaces=NAMESPACES)
        if len(node) == 1:
            node2 = node[0].find(nspath_eval('gmx:Anchor', NAMESPACES))
            if node2 is not None:  # search gmx:Anchor
                value = node2.get(nspath_eval('xlink:href', NAMESPACES))
            else:  # gmd:title should be WMO_CategoryCode
                value = node[0].text

            assert(value == '%s#WMO_CategoryCode' % CODELIST_PREFIX), self.test_requirement_8_2_1

        # (ii) check valid codelist value

    def test_requirement_8_2_2(self):
        """Keywords from WMO_CategoryCode code list shall be defined as keyword type "theme"."""
        self.test_id = gen_test_id('WMO_CategoryCode-keyword-theme')

    def test_requirement_8_2_3(self):
        """All keywords sourced from a particular keyword thesaurus shall be grouped into a single instance of the MD_Keywords class."""
        self.test_id = gen_test_id('keyword-grouping')

    def test_requirement_8_2_4(self):
        """Each WIS Discovery Metadata record describing geographic data shall include the description of at least one geographic bounding box defining the spatial extent of the data"""
        self.test_id = gen_test_id('geographic-bounding-box')

    def test_requirement_9_1_1(self):
        """A WIS Discovery Metadata record describing data for global exchange via the WIS shall indicate the scope of distribution using the keyword "GlobalExchange" of type "dataCenterdataCentre" from thesaurus WMO_DistributionScopeCode."""
        self.test_id = gen_test_id('identification-of-globally-exchanged-data')

    def test_requirement_9_2_1(self):
        """A WIS Discovery Metadata record describing data for global exchange via the WIS shall have a gmd:MD_Metadata/gmd:fileIdentifier attribute formatted as follows (where {uid} is a unique identifier derived from the GTS bulletin or file name): urn:x-wmo:md:int.wmo.wis::{uid}."""
        self.test_id = gen_test_id('fileIdentifier-for-globally-exchanged-data')

    def test_requirement_9_3_1(self):
        """A WIS Discovery Metadata record describing data for global exchange via the WIS shall indicate the WMO Data License as Legal Constraint (type: "otherConstraints") using one and only one term from the WMO_DataLicenseCode code list."""
        self.test_id = gen_test_id('WMO-data-policy-for-globally-exchanged-data')

    def test_requirement_9_3_2(self):
        """A WIS Discovery Metadata record describing data for global exchange via the WIS shall indicate the GTS Priority as Legal Constraint (type: "otherConstraints") using one and only one term from the WMO_GTSProductCategoryCode code list."""
        self.test_id = gen_test_id('GTS-priority-for-globally-exchanged-data')
