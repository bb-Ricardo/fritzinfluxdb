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

sensitive_keys = [
    "token",
    "password"
]


class InfluxDBConfig(ConfigBase):
    """
        class which defines the InfluxDB config options
    """

    version = {
        "type": int,
        "default": 1
    }
    hostname = {
        "type": str,
        "alt": "host",
        "default": None
    }
    port = {
        "type": int,
        "default": 8086
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
    measurement_name = {
        "type": str,
        "default": "fritzbox"
    }

    # version 1 parameters
    username = {
        "type": str,
        "default": None
    }
    password = {
        "type": str,
        "default": None
    }
    database = {
        "type": str,
        "default": None
    }

    # version 2 parameters
    token = {
        "type": str,
        "default": None
    }
    organisation = {
        "type": str,
        "default": None
    }
    bucket = {
        "type": str,
        "default": None
    }

    config_section_name = "influxdb"

    def parse_config(self, config_data: configparser.ConfigParser):

        super().parse_config(config_data)

        # validate data
        mandatory_keys = list()
        if self.version == 1:
            mandatory_keys = ["hostname", "username", "password", "database"]
        elif self.version == 2:
            mandatory_keys = ["hostname", "token", "organisation", "bucket"]
        else:
            log.error(f"Invalid InfluxDB version '{self.version}'.")
            self.parser_error = True

        for key in mandatory_keys:
            if getattr(self, key) is None or len(getattr(self, key)) == 0:
                self.parser_error = True
                log.error(f"InfluxDB {key} not defined")
