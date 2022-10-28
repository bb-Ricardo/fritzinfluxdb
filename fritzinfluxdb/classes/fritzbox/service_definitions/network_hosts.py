# -*- coding: utf-8 -*-
#  Copyright (c) 2022 - 2022 Ricardo Bartels. All rights reserved.
#
#  fritzinfluxdb.py
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see file LICENSE.txt included in this
#  repository or visit: <https://opensource.org/licenses/MIT>.

import re

from fritzinfluxdb.classes.fritzbox.service_definitions import lua_services

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


def prepare_json_response_data(response):
    """
    handler to prepare returned json data for parsing
    """

    return response.json()


# every 2 minutes
lua_services.append(
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
        "response_parser": prepare_json_response_data,
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
lua_services.append({
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
        "response_parser": prepare_json_response_data,
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
