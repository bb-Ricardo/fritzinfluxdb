# -*- coding: utf-8 -*-
#
#  fritzinfluxdb.py
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see file LICENSE.txt included in this
#  repository or visit: <https://opensource.org/licenses/MIT>.

import logging
import sys

from fritzinfluxdb.common import do_error_exit

# define valid log levels
valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]


def get_logger():
    """
    common function to retrieve common log handler in project files

    Returns
    -------
    log handler
    """

    return logging.getLogger("fritzinfluxdb")


def setup_logging(log_level=None, run_as_daemon=False):
    """
    Set up logging for the whole program and return a log handler

    Parameters
    ----------
    log_level: str
        valid log level to set logging to
    run_as_daemon: bool
        define if tool is running as daemon to omit log time stamp

    Returns
    -------
    log handler to use for logging
    """

    if log_level is None or log_level == "":
        do_error_exit("log level undefined or empty. Check config please.")

    # check set log level against self defined log level array
    if not log_level.upper() in valid_log_levels:
        do_error_exit(f"Invalid log level: {log_level}")

    numeric_log_level = getattr(logging, log_level.upper(), None)

    log_format = '%(levelname)s: %(message)s'
    if run_as_daemon is False:
        log_format = f'%(asctime)s - {log_format}'

    log_format = logging.Formatter(log_format)

    # create logger instance
    logger = get_logger()

    logger.setLevel(numeric_log_level)

    log_stream = logging.StreamHandler(sys.stdout)
    log_stream.setFormatter(log_format)
    logger.addHandler(log_stream)

    return logger

# EOF
