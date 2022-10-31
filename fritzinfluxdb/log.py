# -*- coding: utf-8 -*-
#  Copyright (c) 2022 - 2022 Ricardo Bartels. All rights reserved.
#
#  fritzinfluxdb.py
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see file LICENSE.txt included in this
#  repository or visit: <https://opensource.org/licenses/MIT>.

import logging
from logging.handlers import QueueHandler
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


def setup_logging(log_level=None, run_as_daemon=False, log_queue=None):
    """
    Set up logging for the whole program and return a log handler

    Parameters
    ----------
    log_level: str
        valid log level to set logging to
    run_as_daemon: bool
        define if tool is running as daemon to omit log time stamp
    log_queue: asyncio.Queue
        queue object to write logs to which should be sent to InfluxDB

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

    # add handler to write logs to stdout
    log_stream = logging.StreamHandler(sys.stdout)
    log_stream.setFormatter(log_format)
    logger.addHandler(log_stream)

    # add handler to write logs to InfluxDB log queue
    queue_handler = QueueHandler(log_queue)
    queue_handler.setLevel(logging.INFO)
    logger.addHandler(queue_handler)

    return logger

# EOF
