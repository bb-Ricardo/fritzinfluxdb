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
                        help="define config file (default: " + default_config + ")")
    args = parser.parse_args()
    return args


def shutdown(signal, frame):
    global running
    running = False


def query_points(fc, services):
    result = {}

    for service, content in services.items():

        for action in content['actions']:

            if 'value_instances' in content:

                this_result = fc.call_action(service, action)

                for instance in content['value_instances']:

                    rewrite_name = None

                    if ':' in instance:
                        instance, rewrite_name = instance.split(':')
                        instance = instance.strip()
                        rewrite_name = rewrite_name.strip()

                    if instance in this_result:
                        if rewrite_name != None:
                            try:
                                result.update({rewrite_name: int(this_result[instance])})
                            except ValueError:
                                result.update({rewrite_name: this_result[instance]})
                        else:
                            result.update({instance: int(this_result[instance])})
            else:
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


def get_services(config, section_name_start):
    this_sections = [s for s in config.sections() if s.startswith(section_name_start)]
    this_services = {}
    for s in this_sections:
        this_services.update({config.get(s, 'service'): {'actions': config.get(s, 'actions').split("\n")}})
        if config.has_option(s, 'value_instances'):
            this_services[config.get(s, 'service')].update(
                {'value_instances': config.get(s, 'value_instances').split("\n")})

    return this_services


def main():
    signal.signal(signal.SIGTERM, shutdown)

    # set logging
    logging.basicConfig(level=logging.INFO)

    # parse command line arguments
    args = parse_args()

    # check if config file exists
    if not os.path.isfile(args.config_file):
        logging.error("config file \"%s\" not found" % args.config_file)
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

    # create unauthenticated FB client handler
    fritz_client_unauth = fritzconnection.FritzConnection(
        address=config.get('fritzbox', 'host'),
        port=config.get('fritzbox', 'port'),
    )

    # test connection
    if fritz_client_unauth.modelname is None:
        logging.error("Failed to connect to %s" % config.get('fritzbox', 'host'))
        exit(1)

    # create authenticated FB client handler
    fritz_client_auth = fritzconnection.FritzConnection(
        address=config.get('fritzbox', 'host'),
        port=config.get('fritzbox', 'port'),
        user=config.get('fritzbox', 'username'),
        password=config.get('fritzbox', 'password')
    )

    # test connection
    if fritz_client_auth.modelname is None:
        logging.error("Failed to connect to %s" % config.get('fritzbox', 'host'))
        exit(1)

    # read services from config file
    unauth_services = get_services(config, "service")
    auth_services = get_services(config, "auth_service")

    while running:
        points = query_points(fritz_client_unauth, unauth_services)
        points.update(query_points(fritz_client_auth, auth_services))
        data = {
            "measurement": config.get('influxdb', 'measurement_name'),
            "time": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            "fields": points
        }
        try:
            influxdb_client.write_points([data], time_precision="ms")
        except Exception:
            logging.error("Failed to write to InfluxDB %s" % config.get('influxdb', 'host'))

        # just sleep for 10 seconds
        time.sleep(10)


if __name__ == "__main__":
    main()
