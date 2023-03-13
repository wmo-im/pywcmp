# pywcmp

[![Build Status](https://github.com/wmo-im/pywcmp/workflows/build%20%E2%9A%99%EF%B8%8F/badge.svg)](https://github.com/wmo-im/pywcmp/actions)

# WMO Core Metadata Profile Test Suite

pywcmp provides validation and quality assessment capabilities for the [WMO
WIS](https://community.wmo.int/activity-areas/wis/wis-overview) Core Metadata
Profile (WCMP).

- validation against [WCMP 1.3](http://wis.wmo.int/2013/metadata/version_1-3-0/WMO_Core_Metadata_Profile_v1.3_Part_1.pdf), specifically [Part 2](http://wis.wmo.int/2013/metadata/version_1-3-0/WMO_Core_Metadata_Profile_v1.3_Part_2.pdf), Section 2, implementing an executable test suite against the ATS
- validation against [WCMP 2 (draft)](https://github.com/wmo-im/wcmp2), specifically [Annex A: Conformance Class Abstract Test Suite](https://wmo-im.github.io/wcmp2/standard/wcmp2-DRAFT.html#_conformance_class_abstract_test_suite_normative), implementing an executable test suite against the ATS
- quality assessement against the [WCMP Key Performance Indicators](https://community.wmo.int/activity-areas/wis/wis-metadata-kpis)

## Installation

### pip

Install latest stable version from [PyPI](https://pypi.org/project/pywcmp).

```bash
pip3 install pywcmp
```

### From source

Install latest development version.

```bash
python3 -m venv pywcmp
cd pywcmp
. bin/activate
git clone https://github.com/wmo-im/pywcmp.git
cd pywcmp
pip3 install -r requirements.txt
python3 setup.py install
```

## Running

From command line:
```bash
# fetch version
pywcmp --version

# sync supporting configuration bundle (schemas, topics, etc.)
pywcmp bundle sync

# abstract test suite

# validate WCMP 1.3 metadata against abstract test suite (file on disk)
pywcmp ets validate /path/to/file.xml

# validate WCMP 1.3 metadata against abstract test suite (URL)
pywcmp ets validate https://example.org/path/to/file.xml

# validate WCMP 2 metadata against abstract test suite (URL)
pywcmp ets validate https://example.org/path/to/file.json

# adjust debugging messages (CRITICAL, ERROR, WARNING, INFO, DEBUG) to stdout
pywcmp ets validate https://example.org/path/to/file.xml --verbosity DEBUG

# write results to logfile
pywcmp ets validate https://example.org/path/to/file.json --verbosity DEBUG --logfile /tmp/foo.txt

# key performance indicators

# all key performance indicators at once # note: running KPIs automatically runs the ets
pywcmp kpi validate https://example.org/path/to/file.xml --verbosity DEBUG

# all key performance indicators at once, in summary
pywcmp kpi validate https://example.org/path/to/file.xml --verbosity DEBUG --summary

# all key performance indicators at once, with scoring rubric grouping
pywcmp kpi validate https://example.org/path/to/file.xml --verbosity DEBUG --group

# selected key performance indicator
pywcmp kpi validate --kpi 4 /path/to/file.xml -v INFO

# WIS2 topic hierarchies

# validate a WIS2 topic hierarchy
pywcmp topics validate origin.a.wis2.can

# validate a partial WIS2 topic hierarchy
pywcmp topics validate wis2.can --fuzzy

# list children of a given WIS2 topic hierarchy level
pywcmp topics list wis2.a

```

## Using the API
```pycon
>>> # test a file on disk
>>> from lxml import etree
>>> from pywcmp.ets import ets
>>> exml = etree.parse('/path/to/file.xml')
>>> # test ETS
>>> ts = ets.WMOCoreMetadataProfileTestSuite13(exml)
>>> ts.run_tests()  # raises ValueError error stack on exception
>>> # test a URL
>>> from urllib2 import urlopen
>>> from StringIO import StringIO
>>> content = StringIO(urlopen('https://....').read())
>>> exml = etree.parse(content)
>>> ts = ets.WMOCoreMetadataProfileTestSuite13(exml)
>>> ts.run_tests()  # raises ValueError error stack on exception
>>> # handle pywcmp.errors.TestSuiteError
>>> # pywcmp.errors.TestSuiteError.errors is a list of errors
>>> try:
...    ts.run_tests()
... except pywcmp.errors.TestSuiteError as err:
...    print('\n'.join(err.errors))
>>> ...
>>> # test KPI
>>> from pywcmp.kpi import WMOCoreMetadataProfileKeyPerformanceIndicators
>>> kpis = WMOCoreMetadataProfileKeyPerformanceIndicators(exml)
>>> results = kpis.evaluate()
>>> results['summary']
>>> # scoring rubric
>>> grouped = group_kpi_results(results)
```

## Development

```bash
python3 -m venv pywcmp
cd pywcmp
source bin/activate
git clone https://github.com/wmo-im/pywcmp.git
pip3 install -r requirements.txt
pip3 install -r requirements-dev.txt
python3 setup.py install
```

### Running tests

```bash
# via setuptools
python3 setup.py test
# manually
python3 tests/run_tests.py
```

## Releasing

```bash
# create release (x.y.z is the release version)
vi pywcmp/__init__.py  # update __version__
git commit -am 'update release version x.y.z'
git push origin main
git tag -a x.y.z -m 'tagging release version x.y.z'
git push --tags

# upload to PyPI
rm -fr build dist *.egg-info
python setup.py sdist bdist_wheel --universal
twine upload dist/*

# publish release on GitHub (https://github.com/wmo-im/pywcmp/releases/new)

# bump version back to dev
vi pywcmp/__init__.py  # update __version__
git commit -am 'back to dev'
git push origin main
```

## Code Conventions

[PEP8](https://www.python.org/dev/peps/pep-0008)

## Issues

Issues are managed at https://github.com/wmo-im/pywcmp/issues

## Contact

* [Tom Kralidis](https://github.com/tomkralidis)
* [Ján Osuský](https://github.com/josusky)
