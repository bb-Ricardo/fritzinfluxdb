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


class CallLogConfig:

    def __init__(self, sep, header):

        self.sep = ";"
        self.header_list = list()

        if len(sep) > 0:
            self.sep = sep

        if len(header) > 0:
            self.header_list = [x.strip('"') for x in header.split(self.sep)]


class CallLogEntry:
    """
    parse a single call log entry
    maps columns to be backwards compatible
    """

    call_types = {
        "1": "incoming",
        "2": "unanswered",
        "3": "blocked",
        "4": "outgoing"
    }

    def __init__(self, entry: str, config: CallLogConfig):

        # compute a MD5 hash and use as ID to track and group log data by uid tag
        self._hash = hashlib.md5(entry.encode("UTF-8")).hexdigest()

        entry_dict = dict(zip(config.header_list, entry.split(config.sep)))

        self._call_type = self.call_types.get(entry_dict.get("Typ"), "undefined")
        self._date_time = datetime.strptime(entry_dict.get("Datum"), '%d.%m.%y %H:%M')
        self._caller_name = entry_dict.get("Name", "")
        self._caller_number = entry_dict.get("Rufnummer", "")
        self._caller_location = entry_dict.get("Landes-/Ortsnetzbereich", "")
        self._extension = entry_dict.get("Nebenstelle", "")
        self._number_called = entry_dict.get("Eigene Rufnummer", "")
        self._duration = self.get_call_duration(entry_dict.get("Dauer"))

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

    @property
    def hash(self) -> str:
        return self._hash

    @property
    def type(self) -> str:
        return self._call_type

    @property
    def date_time(self) -> datetime:
        return self._date_time

    @property
    def caller_name(self) -> str:
        return self._caller_name.strip('"')

    @property
    def caller_number(self) -> str:
        return self._caller_number.strip('"')

    @property
    def caller_location(self) -> str:
        return self._caller_location.strip('"')

    @property
    def extension(self) -> str:
        return self._extension.strip('"')

    @property
    def number_called(self) -> str:
        return self._number_called.strip('"')

    @property
    def duration(self) -> int:
        return self._duration


class CallLog:
    """
    Parse FritzBox call log entries csv list
    extracts separator and header, parses each line with given seperator
    """

    new_line_char = "\n"

    def __init__(self, data):

        self.entries = list()
        if not isinstance(data, str):
            return

        lines = data.split(self.new_line_char)

        if len(lines) == 0:
            return

        sep = ""
        header = ""

        # extract separator
        if lines[0].startswith("sep="):
            sep = lines[0].split("=")[-1]
            lines = lines[1:]

        # extract header
        if lines[0].strip('"').startswith("Typ"):
            header = lines[0]
            lines = lines[1:]

        config = CallLogConfig(sep, header)

        if len(config.header_list) == 0:
            return

        for line in lines:
            if len(line) == 0:
                continue

            self.entries.append(CallLogEntry(line, config))


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
        "response_parser": lambda response: CallLog(response.text).entries,
        "interval": read_interval,
        "track": True,
        "value_instances": {
            "call_list_type": {
                "type": list,
                "value_function": lambda data: data,
                "next": {
                    "type": str,
                    "tags_function": lambda entry: {"uid": entry.hash},
                    "value_function": lambda entry: entry.type,
                    "timestamp_function": lambda entry: entry.date_time,
                }
            },
            "call_list_caller_name": {
                "type": list,
                "value_function": lambda data: data,
                "next": {
                    "type": str,
                    "tags_function": lambda entry: {"uid": entry.hash},
                    "value_function": lambda entry: entry.caller_name,
                    "timestamp_function": lambda entry: entry.date_time,
                }
            },
            "call_list_caller_number": {
                "type": list,
                "value_function": lambda data: data,
                "next": {
                    "type": str,
                    "tags_function": lambda entry: {"uid": entry.hash},
                    "value_function": lambda entry: entry.caller_number,
                    "timestamp_function": lambda entry: entry.date_time,
                }
            },
            "call_list_caller_location": {
                "type": list,
                "value_function": lambda data: data,
                "next": {
                    "type": str,
                    "tags_function": lambda entry: {"uid": entry.hash},
                    "value_function": lambda entry: entry.caller_location,
                    "timestamp_function": lambda entry: entry.date_time,
                }
            },
            "call_list_extension": {
                "type": list,
                "value_function": lambda data: data,
                "next": {
                    "type": str,
                    "tags_function": lambda entry: {"uid": entry.hash},
                    "value_function": lambda entry: entry.extension,
                    "timestamp_function": lambda entry: entry.date_time,
                }
            },
            "call_list_number_called": {
                "type": list,
                "value_function": lambda data: data,
                "next": {
                    "type": str,
                    "tags_function": lambda entry: {"uid": entry.hash},
                    "value_function": lambda entry: entry.number_called,
                    "timestamp_function": lambda entry: entry.date_time,
                }
            },
            "call_list_duration": {
                "type": list,
                "value_function": lambda data: data,
                "next": {
                    "type": int,
                    "tags_function": lambda entry: {"uid": entry.hash},
                    "value_function": lambda entry: entry.duration,
                    "timestamp_function": lambda entry: entry.date_time,
                }
            }
        }
    }
)
