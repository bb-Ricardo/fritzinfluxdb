# -*- coding: utf-8 -*-
#  Copyright (c) 2022 - 2022 Ricardo Bartels. All rights reserved.
#
#  fritzinfluxdb.py
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see file LICENSE.txt included in this
#  repository or visit: <https://opensource.org/licenses/MIT>.

import pytz
from datetime import datetime
import configparser
import os

from fritzinfluxdb.common import do_error_exit
from fritzinfluxdb.log import get_logger

log = get_logger()


class FritzMeasurement:
    """
        This class holds measurements which should be sanitized to this specification
        https://docs.influxdata.com/influxdb/v2.1/reference/syntax/line-protocol/
    """

    default_box_tag_key = "box"

    __slots__ = ("name", "value", "box_tag", "timestamp", "additional_tags")

    def __init__(self, key, value, data_type=None, box_tag=None, additional_tags=None, timestamp=None):

        # name and primary tag should always be present
        self.name = str(key)
        self.box_tag = str(box_tag)
        self.value = None

        if data_type is not None:
            # noinspection PyBroadException
            try:
                self.value = data_type(value)
            except Exception:
                pass

        if self.value is None:
            self.value = self.sanitize_value(value)

        if timestamp is not None and isinstance(timestamp, datetime):
            self.timestamp = timestamp
        else:
            self.timestamp = datetime.now(pytz.utc)

        self.additional_tags = None

        if isinstance(additional_tags, dict):
            self.additional_tags = additional_tags

    def __repr__(self):
        return f"{self.timestamp}: {self.name}={self.value} ({self.tags})"

    def sanitize_value(self, value):

        if value is None:
            return 0

        if isinstance(value, (int, bool, float)):
            return value

        if not isinstance(value, str):
            log.error(f"Returned value '{value}' for '{self.name}' has incompatible type '{type(value)}', "
                      f"returning '0'")
            return 0

        if "." in value:
            # noinspection PyBroadException
            try:
                # try to convert value to int
                return float(value)
            except Exception:
                pass

        # noinspection PyBroadException
        try:
            # try to convert value to int
            return int(value)
        except Exception:
            pass

        return value.strip()

    @property
    def tags(self):

        tags = dict()
        if self.box_tag is not None:
            tags[self.default_box_tag_key] = self.box_tag

        if self.additional_tags is not None:
            tags = {**tags, **self.additional_tags}

        return tags

    def __hash__(self):
        return hash(self.__repr__())


class ConfigBase:
    """
        Base class to parse config data
    """

    sensitive_keys = [
        "password",
        "token",
        "password"
    ]

    not_config_vars = [
        "config_section_name",
        "__module__",
        "__doc__"
    ]

    parser_error = False

    def __init__(self, config_data: configparser.ConfigParser):

        if not isinstance(config_data, configparser.ConfigParser):
            do_error_exit("config data is not a config parser object")

        self.parse_config(config_data)

    @staticmethod
    def to_bool(value):
        """
            converts a string to a boolean
        """
        valid = {
             'true': True, 't': True, '1': True,
             'false': False, 'f': False, '0': False,
             }

        if isinstance(value, bool):
            return value

        elif isinstance(value, str):
            if value.lower() in valid:
                return valid[value.lower()]

        raise ValueError

    def parse_config(self, config_data):
        """
            generic method to parse config data and also takes care of reading equivalent env var
        """

        config_section_name = getattr(self.__class__, "config_section_name")

        if config_section_name is None:
            raise KeyError(f"Class '{self.__class__.__name__}' is missing 'config_section_name' attribute")

        for config_option in [x for x in vars(self.__class__) if x not in self.__class__.not_config_vars]:

            var_config = getattr(self.__class__, config_option)

            if not isinstance(var_config, dict):
                continue

            var_type = var_config.get("type", str)
            var_alt = var_config.get("alt")
            var_default = var_config.get("default")

            config_value = config_data.get(config_section_name, config_option, fallback=None)
            if config_value is None and var_alt is not None:
                config_value = config_data.get(config_section_name, var_alt, fallback=None)

            config_value = os.environ.get(f"{config_section_name}_{config_option}".upper(), config_value)

            if config_value is not None and var_type == bool:
                try:
                    config_value = self.to_bool(config_value)
                except ValueError:
                    log.error(f"Unable to parse '{config_value}' for '{config_option}' as bool")
                    config_value = var_default

            elif config_value is not None and var_type == int:
                try:
                    config_value = int(config_value)
                except ValueError:
                    log.error(f"Unable to parse '{config_value}' for '{config_option}' as int")
                    config_value = var_default

            else:
                if config_value is None:
                    config_value = var_default

            debug_value = config_value
            if isinstance(debug_value, str) and config_option in self.sensitive_keys:
                debug_value = config_value[0:3] + "***"

            log.debug(f"Config: {config_section_name}.{config_option} = {debug_value}")

            setattr(self, config_option, config_value)
