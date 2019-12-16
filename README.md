[![Build Status](https://travis-ci.org/wmo-im/pywmcp.png?branch=master)](https://travis-ci.org/wmo-im/pywmcp)

# WMO Core Metadata Profile Test Suite

This library implements validation against [WMO Core Metadata Profile 1.3](http://wis.wmo.int/2013/metadata/version_1-3-0/WMO_Core_Metadata_Profile_v1.3_Part_1.pdf), specifically [Part 2](http://wis.wmo.int/2013/metadata/version_1-3-0/WMO_Core_Metadata_Profile_v1.3_Part_2.pdf), Section 2.

## Installation

```bash
python3 -m venv pywmcp
cd pywmcp
. bin/activate
git clone https://github.com/wmo-im/pywmcp.git
cd pywmcp
pip install -r requirements.txt
python setup.py build
python setup.py install
```

## Running

From command line:
```bash
# fetch version
pywmcp --version

# validate metadata against abstract test suite (file on disk)
pywmcp validate ats --file /path/to/file.xml

# validate metadata against abstract test suite (URL)
pywmcp validate ats --url http://example.org/path/to/file.xml

# adjust debugging messages (CRITICAL, ERROR, WARNING, INFO, DEBUG) to stdout
pywmcp validate ats --url http://example.org/path/to/file.xml --verbosity DEBUG

# write results to logfile
pywmcp validate ats --url http://example.org/path/to/file.xml --verbosity DEBUG --logfile /tmp/foo.txt
```

## Using the API
```pycon
# test a file on disk
>>> from lxml import etree
>>> from pywmcp.ats import ats
>>> exml = etree.parse('/path/to/file.xml')
>>> ts = ats.WMOCoreMetadataProfileTestSuite13(exml)
>>> ts.run_tests()  # raises ValueError error stack on exception
# test a URL
>>> from urllib2 import urlopen
>>> from StringIO import StringIO
>>> content = StringIO(urlopen('http://....').read())
>>> exml = etree.parse(content)
>>> ts = ats.WMOCoreMetadataProfileTestSuite13(exml)
>>> ts.run_tests()  # raises ValueError error stack on exception
# handle ats.TestSuiteError
# ats.TestSuiteError.errors is a list of errors
>>> try:
...    ts.run_tests()
... except ats.TestSuiteError as err:
...    print('\n'.join(err.errors))
>>> ...
```

## Development

```bash
python3 -m venv pywmcp
cd pywmcp
source bin/activate
git clone https://github.com/wmo-im/pywmcp.git
pip install -r requirements.txt
pip install -r requirements-dev.txt
python setup.py install
```

### Running tests

```bash
# via setuptools
python setup.py test
# manually
python tests/run_tests.py
```

## Releasing

```bash
python setup.py sdist bdist_wheel --universal
twine upload dist/*
```

## Code Conventions

[PEP8](https://www.python.org/dev/peps/pep-0008)

## Issues

Issues are managed at https://github.com/wmo-im/pywmcp/issues

## Contact

* [Tom Kralidis](https://github.com/tomkralidis)
