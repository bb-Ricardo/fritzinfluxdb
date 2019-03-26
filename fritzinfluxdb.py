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
import logging

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
    config.read(filename)
    return config

def check_db_status(db_handler, db_name):

    try:
        dblist = db_handler.get_list_database()
        db_found = False
        for db in dblist:
            if db['name'] == db_name:
                db_found = True
        if not db_found:
            logging.info('Database <%s> not found, trying to create it', db_name)
            db_handler.create_database(db_name)
        return True
    except Exception as e:
        logging.error('Error creating database: %s', e)
        return False

def main():
    signal.signal(signal.SIGTERM, shutdown)

    # set logging
    logging.basicConfig(level=logging.INFO)

    # parse command line arguments
    args = parse_args()

    # check if config file exists
    if not os.path.isfile(args.config_file):
        sys.stderr.write("Error: config file \"" + args.config_file + "\" not found.\n")
        exit(1)

    # read config from ini file
    config = read_config(args.config_file)

    # set up influxdb handler
    influxdb_client = influxdb.InfluxDBClient(
        config.get('influxdb', 'host'),
        config.getint('influxdb', 'port'),
        config.get('influxdb', 'username'),
        config.get('influxdb', 'password'),
        config.get('influxdb', 'database'),
    )

    # check influx db status
    check_db_status(influxdb_client, config.get('influxdb', 'database'))

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
