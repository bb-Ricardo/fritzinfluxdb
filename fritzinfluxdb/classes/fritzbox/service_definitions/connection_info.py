# -*- coding: utf-8 -*-
#  Copyright (c) 2022 - 2022 Ricardo Bartels. All rights reserved.
#
#  fritzinfluxdb.py
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see file LICENSE.txt included in this
#  repository or visit: <https://opensource.org/licenses/MIT>.

from fritzinfluxdb.common import grab
from fritzinfluxdb.classes.fritzbox.service_definitions import lua_services


def prepare_json_response_data(response):
    """
    handler to prepare returned json data for parsing
    """

    return response.json()


lua_services.append({
        "name": "DSL Info",
        "os_versions": [
            "7.29",
            "7.30",
            "7.31"
        ],
        "method": "POST",
        "params": {
            "page": "dslOv",
            "xhrId": "all",
            "xhr": 1,
            "useajax": 1
        },
        "response_parser": prepare_json_response_data,
        "interval": 600,
        "value_instances": {
            "dsl_line_length": {
                "data_path": "data.connectionData.lineLength",
                "type": int
            },
            "dsl_dslam_vendor": {
                "data_path": "data.connectionData.dslamId",
                "type": str
            },
            "dsl_dslam_sw_version": {
                "data_path": "data.connectionData.version",
                "type": str
            },
            "dsl_line_mode": {
                "data_path": "data.connectionData.line.0.mode",
                "type": str
            }
        }
    }
)

lua_services.append({
        "name": "Cable Info",
        "os_versions": [
            "7.29",
            "7.30",
            "7.31",
            "7.39",
            "7.50"
        ],
        "method": "POST",
        "params": {
            "page": "docOv",
            "xhrId": "all",
            "xhr": 1
        },
        "response_parser": prepare_json_response_data,
        "interval": 600,
        "value_instances": {
            "cable_cmts_vendor": {
                "data_path": "data.connectionData.externApValue",
                "type": str
            },
            "cable_modem_version": {
                "data_path": "data.connectionData.version",
                "type": str
            },
            "cable_line_mode": {
                "data_path": "data.connectionData.line.0.mode",
                "type": str
            },
            "cable_num_ds_channels": {
                "type": int,
                "value_function": (lambda data:
                                   sum([len(x) for x in grab(data, "data.connectionData.dsFreqs.values",
                                                             fallback=dict()).values()])
                                   ),
            },
            "cable_num_us_channels": {
                "type": int,
                "value_function": (lambda data:
                                   sum([len(x) for x in grab(data, "data.connectionData.usFreqs.values",
                                                             fallback=dict()).values()])
                                   ),
            }
        }
    }
)
