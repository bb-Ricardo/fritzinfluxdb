# -*- coding: utf-8 -*-
#  Copyright (c) 2022 - 2022 Ricardo Bartels. All rights reserved.
#
#  fritzinfluxdb.py
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see file LICENSE.txt included in this
#  repository or visit: <https://opensource.org/licenses/MIT>.

from datetime import datetime

from fritzinfluxdb.classes.fritzbox.service_definitions import lua_services


def prepare_json_response_data(response):
    """
    handler to prepare returned json data for parsing
    """

    return response.json()


lua_services.append(
    {
        "name": "System logs",
        "os_versions": [
            "7.29",
            "7.30",
            "7.31"
        ],
        "method": "POST",
        "params": {
            "filter": 1,
            "page": "log",
            "lang": "de"
        },
        "response_parser": prepare_json_response_data,
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
    })

lua_services.append(
    {
        "name": "System logs",
        "os_versions": [
            "7.39",
            "7.50"
        ],
        "method": "POST",
        "params": {
            "filter": "sys",
            "page": "log",
            "lang": "de"
        },
        "response_parser": prepare_json_response_data,
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
                        datetime.strptime(f'{data.get("date")} {data.get("time")}', '%d.%m.%y %H:%M:%S'),
                    "value_function": lambda data: data.get("msg"),
                    "tags_function": None
                }
            }
        }
    })

lua_services.append(
    {
        "name": "Internet connection logs",
        "os_versions": [
            "7.29",
            "7.30",
            "7.31"
        ],
        "method": "POST",
        "params": {
            "filter": 2,
            "page": "log",
            "lang": "de"
        },
        "response_parser": prepare_json_response_data,
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
    })

lua_services.append(
    {
        "name": "Internet connection logs",
        "os_versions": [
            "7.39",
            "7.50"
        ],
        "method": "POST",
        "params": {
            "filter": "net",
            "page": "log",
            "lang": "de"
        },
        "response_parser": prepare_json_response_data,
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
                        datetime.strptime(f'{data.get("date")} {data.get("time")}', '%d.%m.%y %H:%M:%S'),
                    "value_function": lambda data: data.get("msg"),
                    "tags_function": None
                }
            }
        }
    })

lua_services.append(
    {
        "name": "Telephony logs",
        "os_versions": [
            "7.29",
            "7.30",
            "7.31"
        ],
        "method": "POST",
        "params": {
            "filter": 3,
            "page": "log",
            "lang": "de"
        },
        "response_parser": prepare_json_response_data,
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
    })

lua_services.append(
    {
        "name": "Telephony logs",
        "os_versions": [
            "7.39",
            "7.50"
        ],
        "method": "POST",
        "params": {
            "filter": "fon",
            "page": "log",
            "lang": "de"
        },
        "response_parser": prepare_json_response_data,
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
                        datetime.strptime(f'{data.get("date")} {data.get("time")}', '%d.%m.%y %H:%M:%S'),
                    "value_function": lambda data: data.get("msg"),
                    "tags_function": None
                }
            }
        }
    })

lua_services.append(
    {
        "name": "WLAN logs",
        "os_versions": [
            "7.29",
            "7.30",
            "7.31"
        ],
        "method": "POST",
        "params": {
            "filter": 4,
            "page": "log",
            "lang": "de"
        },
        "response_parser": prepare_json_response_data,
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
    })

lua_services.append(
    {
        "name": "WLAN logs",
        "os_versions": [
            "7.39",
            "7.50"
        ],
        "method": "POST",
        "params": {
            "filter": "wlan",
            "page": "log",
            "lang": "de"
        },
        "response_parser": prepare_json_response_data,
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
                        datetime.strptime(f'{data.get("date")} {data.get("time")}', '%d.%m.%y %H:%M:%S'),
                    "value_function": lambda data: data.get("msg"),
                    "tags_function": None
                }
            }
        }
    })

lua_services.append(
    {
        "name": "USB Devices logs",
        "os_versions": [
            "7.29",
            "7.30",
            "7.31"
        ],
        "method": "POST",
        "params": {
            "filter": 5,
            "page": "log",
            "lang": "de"
        },
        "response_parser": prepare_json_response_data,
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
    })

lua_services.append(
    {
        "name": "USB Devices logs",
        "os_versions": [
            "7.39",
            "7.50"
        ],
        "method": "POST",
        "params": {
            "filter": "usb",
            "page": "log",
            "lang": "de"
        },
        "response_parser": prepare_json_response_data,
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
                        datetime.strptime(f'{data.get("date")} {data.get("time")}', '%d.%m.%y %H:%M:%S'),
                    "value_function": lambda data: data.get("msg"),
                    "tags_function": None
                }
            }
        }
    })
