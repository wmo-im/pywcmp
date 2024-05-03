###############################################################################
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2024 Tom Kralidis
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
###############################################################################

#
# pywcmp as a service
# -------------------
#
# This file is intended to be used as a pygeoapi process plugin which will
# provide pywcmp functionality via OGC API - Processes.
#
# To integrate this plugin in pygeoapi:
#
# 1. ensure pywcmp is installed into the pygeoapi deployment environment
#
# 2. add the processes to the pygeoapi configuration as follows:
#
# pywcmp-wis2-wcmp2-ets:
#     type: process
#     processor:
#         name: pywcmp.pygeoapi_plugin.WCMP2ETSProcessor
#
# pywcmp-wis2-wcmp2-kpi:
#     type: process
#     processor:
#         name: pywcmp.pygeoapi_plugin.WCMP2KPIProcessor
#
# 3. (re)start pygeoapi
#
# The resulting processes will be available at the following endpoints:
#
# /processes/pywcmp-wis2-wcmp2-ets
#
# /processes/pywcmp-wis2-wcmp2-kpi
#
# Note that pygeoapi's OpenAPI/Swagger interface (at /openapi) will also
# provide a developer-friendly interface to test and run requests
#


import logging

from pygeoapi.process.base import BaseProcessor, ProcessorExecuteError

from pywcmp.wcmp2.ets import WMOCoreMetadataProfileTestSuite2
from pywcmp.wcmp2.kpi import WMOCoreMetadataProfileKeyPerformanceIndicators

LOGGER = logging.getLogger(__name__)

PROCESS_WCMP2_ETS = {
    'version': '0.1.0',
    'id': 'pywcmp-wis2-wcmp2-ets',
    'title': {
        'en': 'WCMP2 ETS validator'
    },
    'description': {
        'en': 'Validate a WCMP2 document against the ETS'
    },
    'keywords': ['wis2', 'wcmp2', 'ets', 'test suite', 'metadata'],
    'links': [{
        'type': 'text/html',
        'rel': 'about',
        'title': 'information',
        'href': 'https://wmo-im.github.io/wcmp2',
        'hreflang': 'en-US'
    }],
    'inputs': {
        'record': {
            'title': 'WCMP2 record',
            'description': 'WCMP2 record',
            'schema': {
                'type': 'string'
            },
            'minOccurs': 1,
            'maxOccurs': 1,
            'metadata': None,
            'keywords': ['wcmp2']
        },
        'fail_on_schema_validation': {
            'title': 'Fail on schema validation',
            'description': 'Stop the ETS on failing schema validation',
            'schema': {
                'type': 'boolean',
                'default': True
            },
            'minOccurs': 0,
            'maxOccurs': 1,
            'metadata': None,
            'keywords': ['schema', 'validation']
        }
    },
    'outputs': {
        'result': {
            'title': 'Report of ETS results',
            'description': 'Report of ETS results',
            'schema': {
                'type': 'object',
                'contentMediaType': 'application/json'
            }
        }
    },
    'example': {
        'inputs': {
            'record': {
                '$ref': 'https://raw.githubusercontent.com/wmo-im/pywcmp/master/tests/data/wcmp2-passing.json'  # noqa
            },
            'fail_on_schema_validation': True
        }
    }
}


PROCESS_WCMP2_KPI = {
    'version': '0.1.0',
    'id': 'pywcmp-wis2-wcmp2-kpi',
    'title': {
        'en': 'WCMP2 KPI evaluator'
    },
    'description': {
        'en': 'Validate a WCMP2 document against the KPI suite'
    },
    'keywords': ['wis2', 'wcmp2', 'kpi', 'test suite', 'metadata'],
    'links': [{
        'type': 'text/html',
        'rel': 'about',
        'title': 'information',
        'href': 'https://wmo-im.github.io/wcmp2',
        'hreflang': 'en-US'
    }],
    'inputs': {
        'record': {
            'title': 'WCMP2 record',
            'description': 'WCMP2 record',
            'schema': {
                'type': 'string'
            },
            'minOccurs': 1,
            'maxOccurs': 1,
            'metadata': None,
            'keywords': ['wcmp2']
        }
    },
    'outputs': {
        'result': {
            'title': 'Report of KPI results',
            'description': 'Report of KPI results',
            'schema': {
                'type': 'object',
                'contentMediaType': 'application/json'
            }
        }
    },
    'example': {
        'inputs': {
            'record': {
                '$ref': 'https://raw.githubusercontent.com/wmo-im/pywcmp/master/tests/data/wcmp2-passing.json'  # noqa
            }
        }
    }
}


class WCMP2ETSProcessor(BaseProcessor):
    """WCMP2 ETS"""

    def __init__(self, processor_def):
        """
        Initialize object

        :param processor_def: provider definition

        :returns: pywcmp.pygeoapi_plugin.WCMP2ETSProcessor
        """

        super().__init__(processor_def, PROCESS_WCMP2_ETS)

    def execute(self, data):

        response = None
        mimetype = 'application/json'
        record = data.get('record')
        fail_on_schema_validation = data.get('fail_on_schema_validation', True)

        if record is None:
            msg = 'Missing record'
            LOGGER.error(msg)
            raise ProcessorExecuteError(msg)

        LOGGER.debug('Running ETS against record')
        response = WMOCoreMetadataProfileTestSuite2(record).run_tests(
            fail_on_schema_validation=fail_on_schema_validation)

        return mimetype, response

    def __repr__(self):
        return '<WCMP2ETSProcessor>'


class WCMP2KPIProcessor(BaseProcessor):
    """WCMP2 KPI"""

    def __init__(self, processor_def):
        """
        Initialize object

        :param processor_def: provider definition

        :returns: pywcmp.pygeoapi_plugin.WCMP2KPIProcessor
        """

        super().__init__(processor_def, PROCESS_WCMP2_KPI)

    def execute(self, data):

        response = None
        mimetype = 'application/json'
        record = data.get('record')

        if record is None:
            msg = 'Missing record'
            LOGGER.error(msg)
            raise ProcessorExecuteError(msg)

        LOGGER.debug('Running KPIs against record')
        kpis = WMOCoreMetadataProfileKeyPerformanceIndicators(record)
        response = kpis.evaluate()

        return mimetype, response

    def __repr__(self):
        return '<WCMP2KPIProcessor>'
