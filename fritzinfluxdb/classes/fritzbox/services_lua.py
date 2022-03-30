# -*- coding: utf-8 -*-
#
#  fritzinfluxdb.py
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see file LICENSE.txt included in this
#  repository or visit: <https://opensource.org/licenses/MIT>.

fritzbox_services = [
    {
        "name": "System Stats",
        "page": "ecoStat",
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
    },
    {
        "name": "Energy Stats",
        "page": "energy",
        "value_instances": {
            "energy_consumption": {
                "data_path": "data.drain",
                "type": list,
                "next": {
                    "data_path": "actPerc",
                    "type": int,
                    "tags": [
                        "name"
                    ]
                }
            }
        }
    }
]