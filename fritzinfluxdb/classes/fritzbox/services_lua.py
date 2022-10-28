# -*- coding: utf-8 -*-
#  Copyright (c) 2022 - 2022 Ricardo Bartels. All rights reserved.
#
#  fritzinfluxdb.py
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see file LICENSE.txt included in this
#  repository or visit: <https://opensource.org/licenses/MIT>.

import re
from datetime import datetime

from fritzinfluxdb.common import grab

fritzbox_services = list()

# precompile active_host_txt_regex
#  used this neat tool: https://regex101.com/r/ut4KdU/1
# Needs to match following strings:
#   166 / 150 Mbit/s
#   2,4 GHz, 50 / 836 Mbit/s
#   5 GHz, 50 / 836 Mbit/s
#   2,4 GHz
#   5 GHz
active_host_txt_regex = \
    re.compile(r"((?P<frequency>[0-9,]+) GHz)*(, )*((?P<downstream>\d+) / (?P<upstream>\d+) .*bit.*)*")


def prepare_response_data(response):
    """
    handler to prepare returned data for parsing
    """

    return response.json()


def get_active_host_details(data, desired_value: str, fallback_value):

    property_list = data.get("properties")

    if not isinstance(property_list, list):
        property_list = list()

    txt_list = [x.get("txt") for x in property_list]

    if desired_value == "additional_text":
        return ", ".join(txt_list)

    if desired_value == "is_mesh":
        return True if "Mesh" in txt_list else False

    regex_matches = active_host_txt_regex.match(next((x for x in txt_list if "GHz" in x or "bit" in x), ""))

    if regex_matches is None:
        return fallback_value

    return regex_matches.groupdict(fallback_value).get(desired_value, fallback_value)


fritzbox_services.append(
    {
        "name": "System Stats",
        "os_versions": [
            "7.29",
            "7.30",
            "7.31",
            "7.39",
            "7.50"
        ],
        "method": "POST",
        "params": {
            "page": "ecoStat",
            "lang": "de"
        },
        "response_parser": prepare_response_data,
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

fritzbox_services.append(
    {
        "name": "Energy Stats",
        "os_versions": [
            "7.29",
            "7.30",
            "7.31",
            "7.39",
            "7.50"
        ],
        "method": "POST",
        "params": {
            "page": "energy",
            "lang": "de"
        },
        "response_parser": prepare_response_data,
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

fritzbox_services.append(
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
        "response_parser": prepare_response_data,
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

fritzbox_services.append(
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
        "response_parser": prepare_response_data,
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

fritzbox_services.append(
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
        "response_parser": prepare_response_data,
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

fritzbox_services.append(
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
        "response_parser": prepare_response_data,
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

fritzbox_services.append(
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
        "response_parser": prepare_response_data,
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

fritzbox_services.append(
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
        "response_parser": prepare_response_data,
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

fritzbox_services.append(
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
        "response_parser": prepare_response_data,
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

fritzbox_services.append(
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
        "response_parser": prepare_response_data,
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

fritzbox_services.append(
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
        "response_parser": prepare_response_data,
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

fritzbox_services.append(
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
        "response_parser": prepare_response_data,
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

# every 2 minutes
fritzbox_services.append(
    {
        "name": "Active network hosts",
        "os_versions": [
            "7.29",
            "7.30",
            "7.31",
            "7.39",
            "7.50"
        ],
        "method": "POST",
        "params": {
            "page": "netDev",
            "useajax": 1,
            "xhrId": "all",
            "xhr": 1,
            "initial": True
        },
        "response_parser": prepare_response_data,
        "interval": 120,
        "value_instances": {
            "active_hosts_name": {
                "data_path": "data.active",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": str,
                    "tags_function": lambda data: {"uid": data.get("UID")},
                    "value_function": lambda data: data.get("name")
                }
            },
            "active_hosts_mac": {
                "data_path": "data.active",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": str,
                    "tags_function": lambda data: {"uid": data.get("UID")},
                    "value_function": lambda data: data.get("mac")
                }
            },
            "active_hosts_type": {
                "data_path": "data.active",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": str,
                    "tags_function": lambda data: {"uid": data.get("UID")},
                    "value_function": lambda data: data.get("type")
                }
            },
            "active_hosts_parent": {
                "data_path": "data.active",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": str,
                    "tags_function": lambda data: {"uid": data.get("UID")},
                    "value_function": lambda data: data.get("parent", dict()).get("name")
                }
            },
            "active_hosts_port": {
                "data_path": "data.active",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": str,
                    "tags_function": lambda data: {"uid": data.get("UID")},
                    "value_function": lambda data: data.get("port")
                }
            },
            "active_hosts_ipv4": {
                "data_path": "data.active",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": str,
                    "tags_function": lambda data: {"uid": data.get("UID")},
                    "value_function": lambda data: data.get("ipv4", dict()).get("ip")
                }
            },
            "active_hosts_ipv4_last_used": {
                "data_path": "data.active",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": int,
                    "tags_function": lambda data: {"uid": data.get("UID"), "name": data.get("name")},
                    "value_function": lambda data: data.get("ipv4", dict()).get("lastused", 0)
                }
            },
            "active_hosts_additional_text": {
                "data_path": "data.active",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": str,
                    "tags_function": lambda data: {"uid": data.get("UID"), "name": data.get("name")},
                    "value_function": lambda data: get_active_host_details(data, "additional_text", "")
                }
            },
            "active_hosts_is_mesh": {
                "data_path": "data.active",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": bool,
                    "tags_function": lambda data: {"uid": data.get("UID"), "name": data.get("name")},
                    "value_function": lambda data: get_active_host_details(data, "is_mesh", False)
                }
            },
            "active_hosts_frequency": {
                "data_path": "data.active",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": str,
                    "tags_function": lambda data: {"uid": data.get("UID"), "name": data.get("name")},
                    "value_function": lambda data: get_active_host_details(data, "frequency", "")
                }
            },
            "active_hosts_downstream": {
                "data_path": "data.active",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": int,
                    "tags_function": lambda data: {"uid": data.get("UID"), "name": data.get("name")},
                    "value_function": lambda data: get_active_host_details(data, "downstream", 0)
                }
            },
            "active_hosts_upstream": {
                "data_path": "data.active",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": int,
                    "tags_function": lambda data: {"uid": data.get("UID"), "name": data.get("name")},
                    "value_function": lambda data: get_active_host_details(data, "upstream", 0)
                }
            },
            "num_active_host": {
                "type": int,
                "value_function": lambda data: len(data.get("data", {}).get("active", []))
            }
        }
    }
)

# every 10 minutes
fritzbox_services.append({
        "name": "Passive network hosts",
        "os_versions": [
            "7.29",
            "7.30",
            "7.31",
            "7.39",
            "7.50"
        ],
        "method": "POST",
        "params": {
            "page": "netDev",
            "useajax": 1,
            "xhrId": "cleanup",
            "xhr": 1,
        },
        "response_parser": prepare_response_data,
        "interval": 600,
        "value_instances": {
            "passive_hosts_name": {
                "data_path": "data.passive",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": str,
                    "tags_function": lambda data: {"uid": data.get("UID")},
                    "value_function": lambda data: data.get("name")
                }
            },
            "passive_hosts_mac": {
                "data_path": "data.passive",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": str,
                    "tags_function": lambda data: {"uid": data.get("UID")},
                    "value_function": lambda data: data.get("mac")
                }
            },
            "passive_hosts_port": {
                "data_path": "data.passive",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": str,
                    "tags_function": lambda data: {"uid": data.get("UID")},
                    "value_function": lambda data: data.get("port")
                }
            },
            "passive_hosts_ipv4": {
                "data_path": "data.passive",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": str,
                    "tags_function": lambda data: {"uid": data.get("UID")},
                    "value_function": lambda data: data.get("ipv4", dict()).get("ip")
                }
            },
            "num_passive_host": {
                "type": int,
                "value_function": lambda data: len(data.get("data", {}).get("passive", [])),
            }
        }
    }
)

fritzbox_services.append({
        "name": "VPN Users",
        "os_versions": [
            "7.29",
            "7.30",
            "7.31"
        ],
        "method": "POST",
        "params": {
            "page": "shareVpn",
            "xhrId": "all",
            "xhr": 1,
        },
        "response_parser": prepare_response_data,
        "value_instances": {
            "myfritz_host_name": {
                "data_path": "data.vpnInfo.server",
                "type": str
            },
            "vpn_type": {
                "data_path": "data.vpnInfo.type",
                "type": str
            },
            "vpn_user_connected": {
                "data_path": "data.vpnInfo.userConnections",
                "type": dict,
                "next": {
                    "type": str,
                    "value_function": lambda data: data.get("connected"),
                    "tags_function": lambda data: {"name": data.get("name")}
                },
                "exclude_filter_function": lambda data: not isinstance(grab(data, "data.vpnInfo.userConnections"), dict)
            },
            "vpn_user_active": {
                "data_path": "data.vpnInfo.userConnections",
                "type": dict,
                "next": {
                    "type": str,
                    "value_function": lambda data: data.get("active"),
                    "tags_function": lambda data: {"name": data.get("name")}
                },
                "exclude_filter_function": lambda data: not isinstance(grab(data, "data.vpnInfo.userConnections"), dict)
            },
            "vpn_user_virtual_address": {
                "data_path": "data.vpnInfo.userConnections",
                "type": dict,
                "next": {
                    "type": str,
                    "value_function": lambda data: data.get("virtualAddress"),
                    "tags_function": lambda data: {"name": data.get("name")}
                },
                "exclude_filter_function": lambda data: not isinstance(grab(data, "data.vpnInfo.userConnections"), dict)
            },
            "vpn_user_remote_address": {
                "data_path": "data.vpnInfo.userConnections",
                "type": dict,
                "next": {
                    "type": str,
                    "value_function": lambda data: data.get("address"),
                    "tags_function": lambda data: {"name": data.get("name")}
                },
                "exclude_filter_function": lambda data: not isinstance(grab(data, "data.vpnInfo.userConnections"), dict)
            },
            "vpn_user_num_active": {
                "type": int,
                "value_function": (lambda data:
                                   len(
                                       [x for x in grab(data, "data.vpnInfo.userConnections", fallback=dict()).values()
                                        if x.get("connected") is True]
                                   )
                                   ),
                "exclude_filter_function": lambda data: not isinstance(grab(data, "data.vpnInfo.userConnections"), dict)
            }
        }
    }
)

fritzbox_services.append({
        "name": "VPN Users",
        "os_versions": [
            "7.39",
            "7.50"
        ],
        "method": "POST",
        "params": {
            "page": "shareVpn",
            "xhrId": "all",
            "xhr": 1,
        },
        "response_parser": prepare_response_data,
        "value_instances": {
            "myfritz_host_name": {
                "data_path": "data.init.server",
                "type": str
            },
            "vpn_type": {
                "data_path": "data.init.type",
                "type": str
            },
            "vpn_user_connected": {
                "data_path": "data.init.userConnections",
                "type": dict,
                "next": {
                    "type": str,
                    "value_function": lambda data: data.get("connected"),
                    "tags_function": lambda data: {"name": data.get("name")}
                },
                "exclude_filter_function": lambda data: not isinstance(grab(data, "data.init.userConnections"), dict)
            },
            "vpn_user_active": {
                "data_path": "data.init.userConnections",
                "type": dict,
                "next": {
                    "type": str,
                    "value_function": lambda data: data.get("active"),
                    "tags_function": lambda data: {"name": data.get("name")}
                },
                "exclude_filter_function": lambda data: not isinstance(grab(data, "data.init.userConnections"), dict)
            },
            "vpn_user_virtual_address": {
                "data_path": "data.init.userConnections",
                "type": dict,
                "next": {
                    "type": str,
                    "value_function": lambda data: data.get("virtualAddress"),
                    "tags_function": lambda data: {"name": data.get("name")}
                },
                "exclude_filter_function": lambda data: not isinstance(grab(data, "data.init.userConnections"), dict)
            },
            "vpn_user_remote_address": {
                "data_path": "data.init.userConnections",
                "type": dict,
                "next": {
                    "type": str,
                    "value_function": lambda data: data.get("address"),
                    "tags_function": lambda data: {"name": data.get("name")}
                },
                "exclude_filter_function": lambda data: not isinstance(grab(data, "data.init.userConnections"), dict)
            },
            "vpn_user_num_active": {
                "type": int,
                "value_function": (lambda data:
                                   len(
                                       [x for x in grab(data, "data.init.userConnections", fallback=dict()).values()
                                        if x.get("connected") is True]
                                   )
                                   ),
                "exclude_filter_function": lambda data: not isinstance(grab(data, "data.init.userConnections"), dict)
            }
        }
    }
)

fritzbox_services.append({
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
        "response_parser": prepare_response_data,
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

fritzbox_services.append({
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
        "response_parser": prepare_response_data,
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
