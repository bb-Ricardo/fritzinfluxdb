# -*- coding: utf-8 -*-
#  Copyright (c) 2022 - 2023 Ricardo Bartels. All rights reserved.
#
#  fritzinfluxdb.py
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see file LICENSE.txt included in this
#  repository or visit: <https://opensource.org/licenses/MIT>.

import hashlib
from datetime import datetime

from fritzinfluxdb.classes.fritzbox.service_handler import FritzBoxLuaURLPath
from fritzinfluxdb.classes.fritzbox.service_definitions import lua_services


hash_cache = dict()

read_interval = 60


def get_hash(data):
    """
    compute a MD5 hash and use as ID to track and group log data by uid tag
    """

    hit = hash_cache.get(data)
    if hit is not None:
        return hit

    hash_cache[data] = hashlib.md5(data.encode("UTF-8")).hexdigest()

    return hash_cache.get(data)


def get_date(data):
    return datetime.strptime(data.split(";")[1], '%d.%m.%y %H:%M')


def get_call_type(data):

    call_types = {
        "1": "incoming",
        "2": "unanswered",
        "3": "blocked",
        "4": "outgoing"
    }

    return call_types.get(data.split(";")[0], "undefined")


def get_call_duration(data):
    """
    returns call duration in minutes
    """

    # noinspection PyBroadException
    try:
        hours, minutes = data.split(";")[6].split(":")
        duration = int(hours) * 60 + int(minutes)
    except Exception:
        return 0

    return duration


def prepare_response_data(response):
    """
    handler to prepare returned data for parsing
    """

    # exclude from csv output
    filter_strings = [
        'sep=;',
        'Typ;Datum;Name;Rufnummer;Nebenstelle;Eigene Rufnummer;Dauer',
        ''
    ]

    return [x for x in response.text.split("\n") if x not in filter_strings]


# due to the tracking of measurements multiple short calls from the same number within the same minute
# will be reduced to one entry
lua_services.append(
    {
        "name": "Phone call list",
        "os_min_versions": "7.29",
        "url_path": FritzBoxLuaURLPath.foncalls_list,
        "method": "GET",
        "params": {
            "switchcmd": "getdevicelistinfos",
            "csv": "",
        },
        "response_parser": prepare_response_data,
        "interval": read_interval,
        "track": True,
        "value_instances": {
            "call_list_type": {
                "type": list,
                "value_function": lambda data: data,
                "next": {
                    "type": str,
                    "tags_function": lambda data: {"uid": get_hash(data)},
                    "value_function": get_call_type,
                    "timestamp_function": get_date,
                }
            },
            "call_list_caller_name": {
                "type": list,
                "value_function": lambda data: data,
                "next": {
                    "type": str,
                    "tags_function": lambda data: {"uid": get_hash(data)},
                    "value_function": lambda data: data.split(";")[2],
                    "timestamp_function": get_date,
                }
            },
            "call_list_caller_number": {
                "type": list,
                "value_function": lambda data: data,
                "next": {
                    "type": str,
                    "tags_function": lambda data: {"uid": get_hash(data)},
                    "value_function": lambda data: data.split(";")[3],
                    "timestamp_function": get_date,
                }
            },
            "call_list_extension": {
                "type": list,
                "value_function": lambda data: data,
                "next": {
                    "type": str,
                    "tags_function": lambda data: {"uid": get_hash(data)},
                    "value_function": lambda data: data.split(";")[4],
                    "timestamp_function": get_date,
                }
            },
            "call_list_number_called": {
                "type": list,
                "value_function": lambda data: data,
                "next": {
                    "type": str,
                    "tags_function": lambda data: {"uid": get_hash(data)},
                    "value_function": lambda data: data.split(";")[5],
                    "timestamp_function": get_date,
                }
            },
            "call_list_duration": {
                "type": list,
                "value_function": lambda data: data,
                "next": {
                    "type": int,
                    "tags_function": lambda data: {"uid": get_hash(data)},
                    "value_function": get_call_duration,
                    "timestamp_function": get_date,
                }
            },
        }
    }
)
