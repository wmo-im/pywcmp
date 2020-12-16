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

import io
import os
import re
from setuptools import Command, find_packages, setup
import sys
import zipfile

from lxml import etree

from pywcmp.util import get_userdir, urlopen_


class PyTest(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import subprocess
        errno = subprocess.call([sys.executable, os.path.join('tests',
                                 'run_tests.py')])
        raise SystemExit(errno)


def read(filename, encoding='utf-8'):
    """read file contents"""
    full_path = os.path.join(os.path.dirname(__file__), filename)
    with io.open(full_path, encoding=encoding) as fh:
        contents = fh.read().strip()
    return contents


def get_package_version():
    """get version from top-level package init"""
    version_file = read('pywcmp/__init__.py')
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


USERDIR = get_userdir()

KEYWORDS = [
    'WMO',
    'Metadata',
    'WIS',
    'Test Suite',
]

DESCRIPTION = 'A Python implementation of the test suite for WMO Core Metadata Profile'  # noqa

# ensure a fresh MANIFEST file is generated
if (os.path.exists('MANIFEST')):
    os.unlink('MANIFEST')

print('Downloading WMO ISO XML Schemas and Codelists.xml to {}'.format(
    USERDIR))

if not os.path.exists(USERDIR):
    os.mkdir(USERDIR)
    ZIPFILE_URL = 'https://wis.wmo.int/2011/schemata/iso19139_2007/19139.zip'
    FH = io.BytesIO(urlopen_(ZIPFILE_URL).read())
    with zipfile.ZipFile(FH) as z:
        z.extractall(USERDIR)
    CODELIST_URL = 'https://wis.wmo.int/2012/codelists/WMOCodeLists.xml'

    schema_filename = '{}{}WMOCodeLists.xml'.format(USERDIR, os.sep)

    with open(schema_filename, 'wb') as f:
        f.write(urlopen_(CODELIST_URL).read())

    # because some ISO instances ref both gmd and gmx, create a
    # stub xsd in order to validate
    SCHEMA = etree.Element('schema',
                           elementFormDefault='qualified',
                           version='1.0.0',
                           nsmap={None: 'http://www.w3.org/2001/XMLSchema'})

    schema_wrapper_filename = '{}{}iso-all.xsd'.format(USERDIR, os.sep)

    with open(schema_wrapper_filename, 'wb') as f:
        for uri in ['gmd', 'gmx']:
            namespace = 'http://www.isotc211.org/2005/{}'.format(uri)
            schema_location = 'schema/{}/{}.xsd'.format(uri, uri)

            etree.SubElement(SCHEMA, 'import',
                             namespace=namespace,
                             schemaLocation=schema_location)
        f.write(etree.tostring(SCHEMA, pretty_print=True))
else:
    print('Directory {} exists'.format(USERDIR))


setup(
    name='pywcmp',
    version=get_package_version(),
    description=DESCRIPTION.strip(),
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    license='MIT',
    platforms='all',
    keywords=' '.join(KEYWORDS),
    author='Tom Kralidis',
    author_email='tomkralidis@gmail.com',
    maintainer='Tom Kralidis',
    maintainer_email='tomkralidis@gmail.com',
    url='https://github.com/wmo-im/pywcmp',
    install_requires=read('requirements.txt').splitlines(),
    packages=find_packages(),
    # package_data=PACKAGE_DATA,
    entry_points={
        'console_scripts': [
            'pywcmp=pywcmp:cli'
        ]
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering :: Atmospheric Science',
        'Topic :: Scientific/Engineering :: GIS'
    ],
    cmdclass={'test': PyTest},
    test_suite='tests.run_tests'
)
