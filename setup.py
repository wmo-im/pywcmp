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

from distutils.core import setup, Command
import os
import sys
from io import BytesIO
try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen
import zipfile
from lxml import etree

from wmo_cmp_ts import __version__ as version
from wmo_cmp_ts import util

# set dependencies
with open('requirements.txt') as f:
    INSTALL_REQUIRES = f.read().splitlines()

KEYWORDS = [
    'WMO',
    'Metadata',
    'WIS',
    'Test Suite',
]

DESCRIPTION = '''A Python implementation of the test suite for
    WMO Core Metadata Profile'''

with open('README.md') as f:
    LONG_DESCRIPTION = f.read()

CONTACT = 'OGC Meteorology and Oceanography Domain Working Group'

EMAIL = 'tomkralidis@gmail.com'

SCRIPTS = [os.path.join('bin', 'wmo-metadata-validate.py')]

URL = 'https://github.com/OGCMetOceanDWG/wmo-cmp-ts'

# ensure a fresh MANIFEST file is generated
if (os.path.exists('MANIFEST')):
    os.unlink('MANIFEST')


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


# from https://wiki.python.org/moin/Distutils/Cookbook/AutoPackageDiscovery
def is_package(path):
    """decipher whether path is a Python package"""
    return (
        os.path.isdir(path) and
        os.path.isfile(os.path.join(path, '__init__.py'))
    )


def find_packages(path, base=""):
    """Find all packages in path"""
    packages = {}
    for item in os.listdir(path):
        dir1 = os.path.join(path, item)
        if is_package(dir1):
            if base:
                module_name = "%(base)s.%(item)s" % vars()
            else:
                module_name = item
            packages[module_name] = dir1
            packages.update(find_packages(dir1, module_name))
    return packages

USERDIR = util.get_userdir()

print('Downloading WMO ISO XML Schemas and Codelists.xml to %s' % USERDIR)

if not os.path.exists(USERDIR):
    os.mkdir(USERDIR)
    ZIPFILE_URL = 'http://wis.wmo.int/2011/schemata/iso19139_2007/19139.zip'
    FH = BytesIO(urlopen(ZIPFILE_URL).read())
    with zipfile.ZipFile(FH) as z:
        z.extractall(USERDIR)
    CODELIST_URL = 'http://wis.wmo.int/2012/codelists/WMOCodeLists.xml'

    with open('%s%sWMOCodeLists.xml' % (USERDIR, os.sep), 'wb') as f:
        f.write(urlopen(CODELIST_URL).read())

    # because some ISO instances ref both gmd and gmx, create a
    # stub xsd in order to validate
    SCHEMA = etree.Element('schema',
                           elementFormDefault='qualified',
                           version='1.0.0',
                           nsmap={None: 'http://www.w3.org/2001/XMLSchema'})

    with open('%s%siso-all.xsd' % (USERDIR, os.sep), 'wb') as f:
        for uri in ['gmd', 'gmx']:
            etree.SubElement(SCHEMA, 'import',
                             namespace='http://www.isotc211.org/2005/%s' % uri,
                             schemaLocation='schema/%s/%s.xsd' % (uri, uri))
        f.write(etree.tostring(SCHEMA, pretty_print=True))
else:
    print('Directory exists: %s' % USERDIR)


setup(
    name='wmo-cmp-ts',
    version=version,
    description=DESCRIPTION.strip(),
    long_description=LONG_DESCRIPTION,
    license='MIT',
    platforms='all',
    keywords=' '.join(KEYWORDS),
    author=CONTACT,
    author_email=EMAIL,
    maintainer=CONTACT,
    maintainer_email=EMAIL,
    url=URL,
    install_requires=INSTALL_REQUIRES,
    packages=find_packages('.'),
    # package_data=PACKAGE_DATA,
    scripts=SCRIPTS,
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
