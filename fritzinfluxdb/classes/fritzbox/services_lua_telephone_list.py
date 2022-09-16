# -*- coding: utf-8 -*-
#
#  fritzinfluxdb.py
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see file LICENSE.txt included in this
#  repository or visit: <https://opensource.org/licenses/MIT>.

import hashlib
from datetime import datetime

from fritzinfluxdb.common import grab
from fritzinfluxdb.classes.fritzbox.service_handler import FritzBoxLuaURLPath

fritzbox_services = list()
hash_cache = dict()

read_interval = 60


def get_hash(data):

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

    # noinspection PyBroadException
    try:
        hours, minutes = data.split(";")[6].split(":")
        duration = int(hours) * 60 + int(minutes)
    except Exception:
        return 0

    return duration


# due to the tracking of measurements multiple short calls from the same number in the same minute
# will be reduced to one entry
fritzbox_services.append(
    {
        "name": "Phone call list",
        "page": "empty",
        "os_versions": [
            "7.29",
            "7.30",
            "7.31",
            "7.39"
        ],
        "params": {
            "csv": "",
        },
        "interval": read_interval,
        "url_path": FritzBoxLuaURLPath.foncalls_list,
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