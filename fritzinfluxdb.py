#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  Copyright (c) 2022 - 2023 Ricardo Bartels. All rights reserved.
#
#  fritzinfluxdb.py
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see file LICENSE.txt included in this
#  repository or visit: <https://opensource.org/licenses/MIT>.

self_description = """
Fritz InfluxDB is a tiny daemon written to fetch data from a fritz box router and
writes it to an InfluxDB instance.
"""

# import standard modules
import os
import signal
import asyncio
import sys
from http.client import HTTPConnection


from fritzinfluxdb.cli_parser import parse_command_line
from fritzinfluxdb.log import setup_logging
from fritzinfluxdb.configparser import import_config
from fritzinfluxdb.classes.fritzbox.handler import FritzBoxHandler, FritzBoxLuaHandler
from fritzinfluxdb.classes.influxdb.handler import InfluxHandler, InfluxLogAndConfigWriter

__version__ = "1.2.0"
__version_date__ = "2022-12-23"
__author__ = "Ricardo Bartels <ricardo@bitchbrothers.com>"
__description__ = "fritzinfluxdb"
__license__ = "MIT"
__url__ = "https://github.com/bb-Ricardo/fritzinfluxdb"


# default vars
exit_code = 0
default_config = os.path.join(os.path.dirname(__file__), 'fritzinfluxdb.ini')


async def shutdown(shutdown_signal, loop, log):
    """Cleanup tasks tied to the service's shutdown."""
    log.info(f"Received exit signal {shutdown_signal.name}...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

    for task in tasks:
        task.cancel()

    log.info(f"Cancelling {len(tasks)} outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()


def handle_task_result(task: asyncio.Task) -> None:
    global exit_code

    # noinspection PyBroadException
    try:
        task.result()
    except asyncio.CancelledError:
        pass  # Task cancellation should not be logged as an error.
    except Exception:
        import logging
        logging.exception('Exception raised by task = %r', task)

        # we kill ourself to shut down gracefully
        exit_code = 1
        os.kill(os.getpid(), signal.SIGTERM)


def main():

    # check for correct python version
    if sys.version_info[0] != 3 or sys.version_info[1] < 7:
        print("Error: Python version 3.7 or higher required!", file=sys.stderr)
        exit(1)

    # parse command line arguments
    args = parse_command_line(__version__, __description__, __version_date__, __url__, default_config)

    log_queue = asyncio.Queue()
    log = setup_logging("DEBUG" if args.verbose > 0 else "INFO", args.daemon, log_queue)

    log.propagate = False

    log.info(f"Starting {__description__} v{__version__} ({__version_date__})")

    # read config from ini file
    config = import_config(args.config_file, default_config)

    # switch on http verbose
    if args.verbose >= 2:
        HTTPConnection.debuglevel = 1

    # initialize handler
    influx_connection = InfluxHandler(config, user_agent=f"{__description__}/{__version__}")
    fritzbox_connection = FritzBoxHandler(config)
    fritzbox_lua_connection = FritzBoxLuaHandler(fritzbox_connection.config)
    influx_log_writer = InfluxLogAndConfigWriter(fritzbox_connection.config, log_queue)

    handler_list = [
        influx_connection,
        fritzbox_connection,
        fritzbox_lua_connection,
        influx_log_writer
    ]

    for handler in handler_list:
        if handler.config.parser_error is True:
            exit(1)

    log.info("Successfully parsed config")

    # init connection on all handlers
    influx_connection.connect()
    fritzbox_connection.connect()

    # Lua handler is only useful with FritzBox FW >= 7.X
    if fritzbox_connection.config.fw_version is not None and fritzbox_connection.config.fw_version[0] == "7":
        fritzbox_lua_connection.connect()
    else:
        log.info("Disabling queries via Lua. Fritz!OS version must be at least 7.XX")
        handler_list.remove(fritzbox_lua_connection)

    init_errors = False
    for handler in handler_list:
        if handler.init_successful is False:
            log.error(f"Initializing connection to {handler.name} failed")
            init_errors = True

    if init_errors is True:
        exit(1)

    log.info(f"Successfully connected to "
             f"FritzBox '{fritzbox_connection.config.hostname}' ({fritzbox_connection.config.box_tag}) "
             f"Model: {fritzbox_connection.config.model} ({fritzbox_connection.config.link_type}) - "
             f"FW: {fritzbox_connection.config.fw_version}")

    loop = asyncio.get_event_loop()

    for fb_signal in [signal.SIGHUP, signal.SIGTERM, signal.SIGINT]:
        loop.add_signal_handler(
            fb_signal, lambda s=fb_signal: asyncio.create_task(shutdown(s, loop, log)))

    queue = asyncio.Queue()

    log.info("Starting main loop")

    try:
        for handler in handler_list:
            task = loop.create_task(handler.task_loop(queue))
            task.add_done_callback(handle_task_result)
        loop.run_forever()
    finally:
        loop.close()
        fritzbox_connection.close()
        fritzbox_lua_connection.close()
        influx_connection.close()
        log.info(f"Successfully shutdown {__description__}")

    exit(exit_code)


if __name__ == "__main__":
    main()
