# -*- coding: utf-8 -*-
#
#  fritzinfluxdb.py
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see file LICENSE.txt included in this
#  repository or visit: <https://opensource.org/licenses/MIT>.

import os
import configparser

from fritzinfluxdb.log import get_logger
from fritzinfluxdb.common import do_error_exit

log = get_logger()


def import_config(filenames):
    """
    Read config ini files in the given order and return configparser object

    Parameters
    ----------
    filenames: str
        path of ini file to parse

    Returns
    -------
    configparser.ConfigParser(): configparser object
    """

    # check if config file exists
    config_file_errors = False
    for f in filenames:
        if not os.path.isfile(f):
            log.error(f'Config file "{f}" not found')
            config_file_errors = True
            continue

        # check if config file is readable
        if not os.access(f, os.R_OK):
            log.error(f'Config file "{f}" not readable')
            config_file_errors = True
            continue

    if config_file_errors:
        do_error_exit("Unable to open config file.")

    config = configparser.ConfigParser()

    try:
        config.read(filenames)
    except configparser.Error as e:
        do_error_exit(f"Config Error: {e}")

    log.info("Done reading config files")

    return config

# EOF
