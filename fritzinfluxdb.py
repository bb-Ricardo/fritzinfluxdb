#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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


from fritzinfluxdb.cli_parser import parse_command_line
from fritzinfluxdb.log import setup_logging
from fritzinfluxdb.configparser import import_config
from fritzinfluxdb.common import do_error_exit
from fritzinfluxdb.classes.fritzbox.handler import FritzBoxHandler
from fritzinfluxdb.classes.influxdb.handler import InfluxHandler

__version__ = "0.4.0"
__version_date__ = "2020-08-03"
__description__ = "fritzinfluxdb"
__license__ = "MIT"
__url__ = "https://github.com/karrot-dev/fritzinfluxdb"


# default vars
running = True
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


def main():

    # parse command line arguments
    args = parse_command_line(__version__, __description__, __version_date__, __url__, default_config)

    log = setup_logging("DEBUG" if args.verbose is True else "INFO", args.daemon)

    log.propagate = False
#    logging.getLogger("urllib3").propagate = False
#    logging.getLogger('urllib3').setLevel(logging.ERROR)

    # read config from ini file
    config = import_config(args.config_file)

    # initialize handler
    influx_connection = InfluxHandler(config)
    fritzbox_connection = FritzBoxHandler(config)

    log.info("Successfully parsed config")

    influx_connection.connect()

    if influx_connection.init_successful is False:
        do_error_exit("Initializing connection to InfluxDB failed")

    fritzbox_connection.connect()

    if fritzbox_connection.init_successful is False:
        do_error_exit("Initializing connection to FritzBox failed")

    loop = asyncio.get_event_loop()

    for fb_signal in [signal.SIGHUP, signal.SIGTERM, signal.SIGINT]:
        loop.add_signal_handler(
            fb_signal, lambda s=fb_signal: asyncio.create_task(shutdown(s, loop, log)))

    queue = asyncio.Queue()

    log.info("Starting main loop")

    try:
        loop.create_task(fritzbox_connection.query_loop(queue))
        loop.create_task(influx_connection.parse_queue(queue))
        loop.run_forever()
    finally:
        loop.close()
        fritzbox_connection.close()
        influx_connection.close()
        log.info("Successfully shutdown the Mayhem service.")

    exit(0)


if __name__ == "__main__":
    main()
