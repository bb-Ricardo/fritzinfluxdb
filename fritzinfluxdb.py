#!/usr/bin/env python

import os
import sys
import signal
import configparser
import fritzconnection
import influxdb
import time
from datetime import datetime
import argparse

running = True
default_config = os.path.join(os.path.dirname(__file__), 'default.ini')

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", dest="config_file", default=default_config,
                        help="define config file (default: "+default_config+")")
    args = parser.parse_args()
    return args

def shutdown(signal, frame):
    global running
    running = False


def query_points(fc, services):
    result = {}
    for service, actions in services.items():
        for action in actions:
            result.update(fc.call_action(service, action))

    return result


def read_config(filename):
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), 'defaults.ini'))
    config.read(filename)
    return config


def main():
    signal.signal(signal.SIGTERM, shutdown)

    args = parse_args()

    # check if config file exists
    if not os.path.isfile(args.config_file):
        sys.stderr.write("Error: config file \"" + args.config_file + "\" not found.\n")
        exit(1)

    config = read_config(args.config_file)

    influxdb_client = influxdb.InfluxDBClient(
        config.get('influxdb', 'host'),
        config.getint('influxdb', 'port'),
        config.get('influxdb', 'username'),
        config.get('influxdb', 'password'),
        config.get('influxdb', 'database'),
    )
    influxdb_client.create_database(config.get('influxdb', 'database'))

    fritz_client = fritzconnection.FritzConnection(
        address=config.get('fritzbox', 'host'),
        port=config.get('fritzbox', 'port'),
        user=config.get('fritzbox', 'username'),
        password=config.get('fritzbox', 'password')
    )
    if fritz_client.modelname is None:
        raise IOError("fritzinflux: Failed to connect to %s" %
                      config.get('fritzbox', 'host'))

    sections = [s for s in config.sections() if s.startswith('service')]
    services = {}
    for s in sections:
        services.update({config.get(s, 'service'): config.get(s, 'actions').split("\n")})

    while running:
        points = query_points(fritz_client, services)
        data = {
            "measurement": config.get('fritzbox', 'measurement_name'),
            "time": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            "fields": points
        }
        influxdb_client.write_points([data], time_precision="ms")
        time.sleep(10)


if __name__ == "__main__":
    main()
