# -*- coding: utf-8 -*-
#  Copyright (c) 2022 - 2022 Ricardo Bartels. All rights reserved.
#
#  fritzinfluxdb.py
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see file LICENSE.txt included in this
#  repository or visit: <https://opensource.org/licenses/MIT>.

import configparser
import pytz

from fritzinfluxdb.log import get_logger
from fritzinfluxdb.classes.common import ConfigBase

log = get_logger()


class FritzBoxConfig(ConfigBase):
    """
        class which defines the FritzBox config options
    """

    hostname = {
        "type": str,
        "alt": "host",
        "default": "192.168.178.1"
    }
    username = {
        "type": str,
        "default": None
    }
    password = {
        "type": str,
        "default": None
    }
    port = {
        "type": int,
        "default": 49000
    }
    tls_enabled = {
        "type": bool,
        "alt": "ssl",
        "default": False
    }
    verify_tls = {
        "type": bool,
        "alt": "verify_ssl",
        "default": False
    }
    connect_timeout = {
        "type": int,
        "alt": "timeout",
        "default": 10
    }
    request_interval = {
        "type": int,
        "alt": "interval",
        "default": 10
    }
    box_tag = {
        "type": str,
        "default": "fritz.box"
    }
    timezone = {
        "type": str,
        "default": "Europe/Berlin"
    }

    config_section_name = "fritzbox"

    def __init__(self, config_data):

        super().__init__(config_data)

        self._fw_version = None
        self.model = None

    def parse_config(self, config_data: configparser.ConfigParser):

        super().parse_config(config_data)

        min_request_interval = self.__class__.request_interval.get("default")
        if getattr(self, "request_interval") < min_request_interval:
            log.info(f"Setting minimum FritzBox request interval to {min_request_interval} seconds")
            self.request_interval = min_request_interval

        # validate data
        for key in ["username", "password"]:
            if getattr(self, key) is None or len(getattr(self, key)) == 0:
                self.parser_error = True
                log.error(f"FritzBox {key} not defined")

        # noinspection PyBroadException
        try:
            self.timezone = pytz.timezone(self.timezone)
        except Exception as e:
            log.error(f"Defined FritzBox time zone '{self.timezone}' is invalid/unknown")
            self.parser_error = True

        # set TR-069 TLS port if undefined
        if self.tls_enabled is True and self.port == self.__class__.port.get("default"):
            self.port += 443

    @property
    def fw_version(self):
        return self._fw_version

    @fw_version.setter
    def fw_version(self, version):

        # noinspection PyBroadException
        try:
            _, major, minor = f"{version}".split(".")
            self._fw_version = f"{int(major)}.{int(minor)}"
        except Exception:
            pass
