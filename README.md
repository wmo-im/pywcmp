[![Build Status](https://travis-ci.org/OGCMetOceanDWG/wmo-cmp-ts.png?branch=master)](https://travis-ci.org/OGCMetOceanDWG/wmo-cmp-ts)

wmo-cmp-ts
==========

WMO Core Metadata Profile Test Suite

Installation
------------

```bash
virtualenv wmo-cmp-ts
cd wmo-cmp-ts
. bin/activate
git clone git@github.com:OGCMetOceanDWG/wmo-cmp-ts.git
cd wmo-cmp-ts
pip install -r requirements.txt
python setup.py build
python setup.py install
```

Running
-------

```bash
wmo-metadata-validate.py /path/to/file.xml
```
