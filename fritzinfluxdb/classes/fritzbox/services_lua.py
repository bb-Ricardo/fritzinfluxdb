# -*- coding: utf-8 -*-
#
#  fritzinfluxdb.py
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see file LICENSE.txt included in this
#  repository or visit: <https://opensource.org/licenses/MIT>.

from datetime import datetime


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
                    # data struct type: dict
                    "type": int,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": lambda data: data.get("actPerc"),
                    "exclude_filter_function": lambda data: "lan" in data.keys()
                }
            }
        }
    },
    {
        "name": "System logs",
        "page": "log",
        "params": {
            "filter": 1
        },
        "track": True,
        "interval": 60,
        "value_instances": {
            "log_entry": {
                "data_path": "data.log",
                "type": list,
                "next": {
                    # data struct type: list
                    "type": str,
                    "tags": {
                        "log_type": "System"
                    },
                    "timestamp_function": lambda data:
                        datetime.strptime(f'{data[0]} {data[1]}', '%d.%m.%y %H:%M:%S'),
                    "value_function": lambda data: data[2],
                    "tags_function": None
                }
            }
        }
    },
    {
        "name": "Internet connection logs",
        "page": "log",
        "params": {
            "filter": 2
        },
        "track": True,
        "interval": 61,
        "value_instances": {
            "log_entry": {
                "data_path": "data.log",
                "type": list,
                "next": {
                    # data struct type: list
                    "type": str,
                    "tags": {
                        "log_type": "Internet connection"
                    },
                    "timestamp_function": lambda data:
                        datetime.strptime(f'{data[0]} {data[1]}', '%d.%m.%y %H:%M:%S'),
                    "value_function": lambda data: data[2],
                    "tags_function": None
                }
            }
        }
    },
    {
        "name": "Telephony logs",
        "page": "log",
        "params": {
            "filter": 3
        },
        "track": True,
        "interval": 62,
        "value_instances": {
            "log_entry": {
                "data_path": "data.log",
                "type": list,
                "next": {
                    # data struct type: list
                    "type": str,
                    "tags": {
                        "log_type": "Telephony"
                    },
                    "timestamp_function": lambda data:
                        datetime.strptime(f'{data[0]} {data[1]}', '%d.%m.%y %H:%M:%S'),
                    "value_function": lambda data: data[2],
                    "tags_function": None
                }
            }
        }
    },
    {
        "name": "WLAN logs",
        "page": "log",
        "params": {
            "filter": 4
        },
        "track": True,
        "interval": 63,
        "value_instances": {
            "log_entry": {
                "data_path": "data.log",
                "type": list,
                "next": {
                    # data struct type: list
                    "type": str,
                    "tags": {
                        "log_type": "WLAN"
                    },
                    "timestamp_function": lambda data:
                        datetime.strptime(f'{data[0]} {data[1]}', '%d.%m.%y %H:%M:%S'),
                    "value_function": lambda data: data[2],
                    "tags_function": None
                }
            }
        }
    },
    {
        "name": "USB Devices logs",
        "page": "log",
        "params": {
            "filter": 5
        },
        "track": True,
        "interval": 64,
        "value_instances": {
            "log_entry": {
                "data_path": "data.log",
                "type": list,
                "next": {
                    # data struct type: list
                    "type": str,
                    "tags": {
                        "log_type": "USB Devices"
                    },
                    "timestamp_function": lambda data:
                    datetime.strptime(f'{data[0]} {data[1]}', '%d.%m.%y %H:%M:%S'),
                    "value_function": lambda data: data[2],
                    "tags_function": None
                }
            }
        }
    }
]
