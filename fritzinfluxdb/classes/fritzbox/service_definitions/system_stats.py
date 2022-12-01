# -*- coding: utf-8 -*-
#  Copyright (c) 2022 - 2022 Ricardo Bartels. All rights reserved.
#
#  fritzinfluxdb.py
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see file LICENSE.txt included in this
#  repository or visit: <https://opensource.org/licenses/MIT>.

from fritzinfluxdb.classes.fritzbox.service_definitions import lua_services

read_interval = 150


def prepare_json_response_data(response):
    """
    handler to prepare returned json data for parsing
    """

    return response.json()


lua_services.append(
    {
        "name": "System Stats",
        "os_min_versions": "7.29",
        "method": "POST",
        "params": {
            "page": "ecoStat",
            "lang": "de"
        },
        "response_parser": prepare_json_response_data,
        "interval": read_interval,
        "value_instances": {
            "cpu_temp": {
                "data_path": "data.cputemp.series.0.-1",
                "type": int
            },
            "cpu_utilization": {
                "data_path": "data.cpuutil.series.0.-1",
                "type": int
            },
            "ram_usage_fixed": {
                "data_path": "data.ramusage.series.0.-1",
                "type": int
            },
            "ram_usage_dynamic": {
                "data_path": "data.ramusage.series.1.-1",
                "type": int
            },
            "ram_usage_free": {
                "data_path": "data.ramusage.series.2.-1",
                "type": int
            }
        }
    })

lua_services.append(
    {
        "name": "Energy Stats",
        "os_min_versions": "7.29",
        "method": "POST",
        "params": {
            "page": "energy",
            "lang": "de"
        },
        "response_parser": prepare_json_response_data,
        "interval": read_interval,
        "value_instances": {
            "energy_consumption": {
                "data_path": "data.drain",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": int,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": lambda data: data.get("actPerc"),
                    "exclude_filter_function": lambda data: "lan" in data.keys()
                }
            }
        }
    })
