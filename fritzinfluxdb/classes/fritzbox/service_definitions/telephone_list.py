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

call_types = {
    "1": "incoming",
    "2": "unanswered",
    "3": "blocked",
    "4": "outgoing"
}


class CallLogEntry:

    def __init__(self, data: str):

        # compute a MD5 hash and use as ID to track and group log data by uid tag
        self._hash = hashlib.md5(data.encode("UTF-8")).hexdigest()

        data_fields = data.split(";")

        self._call_type = call_types.get(data_fields[0], "undefined")
        self._date_time = datetime.strptime(data_fields[1], '%d.%m.%y %H:%M')
        self._caller_name = data_fields[2]
        self._caller_number = data_fields[3]
        if len(data_fields) == 7:
            self._extension = data_fields[4]
            self._number_called = data_fields[5]
            self._duration = self.get_call_duration(data_fields[6])
        else:
            self._extension = data_fields[5]
            self._number_called = data_fields[6]
            self._duration = self.get_call_duration(data_fields[7])

    @staticmethod
    def get_call_duration(field) -> int:
        """
        returns call duration in minutes
        """

        # noinspection PyBroadException
        try:
            hours, minutes = field.split(":")
            duration = int(hours) * 60 + int(minutes)
        except Exception:
            duration = 0

        return duration

    def hash(self) -> str:
        return self._hash

    def type(self) -> str:
        return self._call_type

    def date_time(self) -> datetime:
        return self._date_time

    def caller_name(self) -> str:
        return self._caller_name

    def caller_number(self) -> str:
        return self._caller_number

    def extension(self) -> str:
        return self._extension

    def number_called(self) -> str:
        return self._number_called

    def duration(self) -> int:
        return self._duration


def prepare_response_data(response):
    """
    handler to prepare returned data for parsing
    """

    # exclude from csv output
    filter_strings = [
        'sep=;',
        'Typ;Datum;Name;Rufnummer;Nebenstelle;Eigene Rufnummer;Dauer',
        'Typ;Datum;Name;Rufnummer;Landes-/Ortsnetzbereich;Nebenstelle;Eigene Rufnummer;Dauer',
        ''
    ]

    return [CallLogEntry(x) for x in response.text.split("\n") if x not in filter_strings]


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
                    "tags_function": lambda entry: {"uid": entry.hash()},
                    "value_function": lambda entry: entry.type(),
                    "timestamp_function": lambda entry: entry.date_time(),
                }
            },
            "call_list_caller_name": {
                "type": list,
                "value_function": lambda data: data,
                "next": {
                    "type": str,
                    "tags_function": lambda entry: {"uid": entry.hash()},
                    "value_function": lambda entry: entry.caller_name(),
                    "timestamp_function": lambda entry: entry.date_time(),
                }
            },
            "call_list_caller_number": {
                "type": list,
                "value_function": lambda data: data,
                "next": {
                    "type": str,
                    "tags_function": lambda entry: {"uid": entry.hash()},
                    "value_function": lambda entry: entry.caller_number(),
                    "timestamp_function": lambda entry: entry.date_time(),
                }
            },
            "call_list_extension": {
                "type": list,
                "value_function": lambda data: data,
                "next": {
                    "type": str,
                    "tags_function": lambda entry: {"uid": entry.hash()},
                    "value_function": lambda entry: entry.extension(),
                    "timestamp_function": lambda entry: entry.date_time(),
                }
            },
            "call_list_number_called": {
                "type": list,
                "value_function": lambda data: data,
                "next": {
                    "type": str,
                    "tags_function": lambda entry: {"uid": entry.hash()},
                    "value_function": lambda entry: entry.number_called(),
                    "timestamp_function": lambda entry: entry.date_time(),
                }
            },
            "call_list_duration": {
                "type": list,
                "value_function": lambda data: data,
                "next": {
                    "type": int,
                    "tags_function": lambda entry: {"uid": entry.hash()},
                    "value_function": lambda entry: entry.duration(),
                    "timestamp_function": lambda entry: entry.date_time(),
                }
            }
        }
    }
)
