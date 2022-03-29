# -*- coding: utf-8 -*-
#
#  fritzinfluxdb.py
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see file LICENSE.txt included in this
#  repository or visit: <https://opensource.org/licenses/MIT>.

import configparser

from fritzinfluxdb.log import get_logger
from fritzinfluxdb.classes.common import ConfigBase

log = get_logger()


class FritzBoxConfig(ConfigBase):

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
    connect_timeout = {
        "type": int,
        "alt": "timeout",
        "default": 5
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

    config_section_name = "fritzbox"

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
