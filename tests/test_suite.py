# -*- coding: ISO-8859-15 -*-

import unittest


def msg(test_id, test_description):
    """Convenience function to print test props"""
    return '%s: %s' % (test_id, test_description)


class WmoCmpTest(unittest.TestCase):
    """Test suite for WMO Core Metadata Profile assertions"""

    def __init__(self, *args, **kwargs):
        """overload to add tid class attr"""
        super(WmoCmpTest, self).__init__(*args, **kwargs)
        self.tid = None

    def id(self):
        """overrides native method to return id as per profile"""
        return 'http://wis.wmo.int/2012/metadata/conf/%s' % self.tid

    def setUp(self):
        """setup test fixtures, etc."""
        print msg(self.id(), self.shortDescription())

    def tearDown(self):
        """return to pristine state"""
        pass

    def test_requirement_6_1_1(self):
        """Requirement 6.1.1: Each WIS Discovery Metadata record shall validate without error against the XML schemas defined in ISO/TS 19139:2007."""
        self.tid = 'ISO-TS-19139-2007-xml-schema-validation'

    def test_requirement_6_1_2(self):
        """Requirement 6.1.2: Each WIS Discovery Metadata record shall validate without error against the rule-based constraints listed in ISO/TS 19139:2007 Annex A (Table A.1)."""
        self.tid = 'ISO-TS-19139-2007-rule-based-validation'

    def test_requirement_6_2_1(self):
        """Requirement 6.2.1: Each WIS Discovery Metadata record shall explicitly name all namespaces used within the record; use of default namespaces is prohibited."""
        self.tid = 'explicit-xml-namespace-identification'

    def test_requirement_6_3_1(self):
        """Requirement 6.3.1: Each WIS Discovery Metadata record shall declare the following XML namespace for GML: http://www.opengis.net/gml/3.2."""
        self.tid = 'gml-namespace-specification'

    def test_requirement_8_1_1(self):
        """Requirement 8.1.1: Each WIS Discovery Metadata record shall include one gmd:MD_Metadata/gmd:fileIdentifier attribute."""
        self.tid = 'fileIdentifier-cardinality'

    def test_requirement_8_2_1(self):
        """Requirement 8.2.1: Each WIS Discovery Metadata record shall include at least one keyword from the WMO_CategoryCode code list."""
        self.tid = 'WMO_CategoryCode-keyword-cardinality'

    def test_requirement_8_2_2(self):
        """Requirement 8.2.2: Keywords from WMO_CategoryCode code list shall be defined as keyword type "theme"."""
        self.tid = 'WMO_CategoryCode-keyword-theme'

    def test_requirement_8_2_3(self):
        """Requirement 8.2.3: All keywords sourced from a particular keyword thesaurus shall be grouped into a single instance of the MD_Keywords class."""
        self.tid = 'keyword-grouping'

    def test_requirement_8_2_4(self):
        """Requirement 8.2.4: Each WIS Discovery Metadata record describing geographic data shall include the description of at least one geographic bounding box defining the spatial extent of the data"""
        self.tid = 'geographic-bounding-box'

    def test_requirement_9_1_1(self):
        """Requirement 9.1.1: A WIS Discovery Metadata record describing data for global exchange via the WIS shall indicate the scope of distribution using the keyword "GlobalExchange" of type "dataCenterdataCentre" from thesaurus WMO_DistributionScopeCode."""
        self.tid = 'identification-of-globally-exchanged-data'

    def test_requirement_9_2_1(self):
        """Requirement 9.2.1: A WIS Discovery Metadata record describing data for global exchange via the WIS shall have a gmd:MD_Metadata/gmd:fileIdentifier attribute formatted as follows (where {uid} is a unique identifier derived from the GTS bulletin or file name): urn:x-wmo:md:int.wmo.wis::{uid}."""
        self.tid = 'fileIdentifier-for-globally-exchanged-data'

    def test_requirement_9_3_1(self):
        """Requirement 9.3.1: A WIS Discovery Metadata record describing data for global exchange via the WIS shall indicate the WMO Data License as Legal Constraint (type: "otherConstraints") using one and only one term from the WMO_DataLicenseCode code list."""
        self.tid = 'WMO-data-policy-for-globally-exchanged-data'

    def test_requirement_9_3_2(self):
        """Requirement 9.3.2: A WIS Discovery Metadata record describing data for global exchange via the WIS shall indicate the GTS Priority as Legal Constraint (type: "otherConstraints") using one and only one term from the WMO_GTSProductCategoryCode code list."""
        self.tid = 'GTS-priority-for-globally-exchanged-data'

if __name__ == '__main__':
    unittest.main()
