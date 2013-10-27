# -*- coding: iso-8859-15 -*-

from distutils.core import setup
import os
from StringIO import StringIO
from urllib2 import urlopen
import zipfile

import wmo_cmp_ts
from wmo_cmp_ts import util

# set dependencies
INSTALL_REQUIRES = [line.strip() for line in open('requirements.txt')]

KEYWORDS = [
    'WMO',
    'Metadata',
    'WIS',
    'Test Suite',
]

DESCRIPTION = '''A Python implementation of the test suite for
    WMO Core Metadata Profile'''

CONTACT = 'OGC Meteorology and Oceanography Domain Working Group'

EMAIL = 'tomkralidis@gmail.com'

SCRIPTS = [os.path.join('bin', 'wmo-metadata-validate.py')]

URL = 'https://github.com/OGCMetOceanDWG/wmo-cmp-ts'


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

print 'Downloading WMO ISO XML Schemas and Codelists.xml'

TEMPDIR = util.get_tempdir()

if not os.path.exists(TEMPDIR):
    os.mkdir(TEMPDIR)
    ZIPFILE_URL = 'http://wis.wmo.int/2011/schemata/iso19139_2007/19139.zip'
    FH = StringIO(urlopen(ZIPFILE_URL).read())
    with zipfile.ZipFile(FH) as z:
        z.extractall(TEMPDIR)
    CODELIST_URL = 'http://wis.wmo.int/2012/codelists/WMOCodeLists.xml'

    with open('%s%sWMOCodeLists.xml' % (TEMPDIR, os.sep), 'w') as f:
        f.write(urlopen(CODELIST_URL).read())

setup(
    name='wmo-cmp-ts',
    version=wmo_cmp_ts.__version__,
    description=DESCRIPTION.strip(),
    long_description=open('README.md').read(),
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
    #package_data=PACKAGE_DATA,
    scripts=SCRIPTS,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering :: Atmospheric Science'
    ]
)
