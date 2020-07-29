#!/usr/bin/env python3

self_description = """
Fritz InfluxDB is a tiny daemon written to fetch data from a fritz box router and
writes it to an InfluxDB instance.
"""

# import standard modules
from argparse import ArgumentParser, RawDescriptionHelpFormatter
import configparser
import logging
import os
import signal
import time
from datetime import datetime

# import 3rd party modules
import fritzconnection
import influxdb


__version__ = "0.1.0"
__version_date__ = "2019-08-12"
__description__ = "fritzinfluxdb"
__license__ = "MIT"


# default vars
running = True
default_config = os.path.join(os.path.dirname(__file__), 'fritzinfluxdb.ini')
default_log_level = logging.INFO


def parse_args():
    """parse command line arguments

    Also add current version and version date to description
    """

    parser = ArgumentParser(
        description=self_description + "\nVersion: " + __version__ + " (" + __version_date__ + ")",
        formatter_class=RawDescriptionHelpFormatter)

    parser.add_argument("-c", "--config", dest="config_file", default=default_config,
                        help="define config file (default: " + default_config + ")")
    parser.add_argument("-d", "--daemon", action='store_true',
                        help="define if the script is run as a systemd daemon")
    parser.add_argument("-v", "--verbose", action='store_true',
                        help="turn on verbose output to get debug logging")

    return parser.parse_args()


# noinspection PyUnusedLocal
def shutdown(exit_signal, frame):
    global running
    running = False


def sanitize_fb_return_data(results):
    """
    sometimes integers are returned as string
    try to sanitize this a bit
    """
    return_results = {}
    for instance in results:
        # turn None => 0
        if results[instance] is None:
            return_results.update({instance: 0})
        else:
            # try to parse as int
            try:
                return_results.update({instance: int(results[instance])})
            # keep it a string if this fails
            except ValueError:
                return_results.update({instance: results[instance]})

    return return_results


def query_points(fc, services):
    result = {}
    error = False

    for service, content in services.items():

        for action in content['actions']:

            if 'value_instances' in content:

                try:
                    this_result = fc.call_action(service, action)
                except fritzconnection.fritzconnection.ServiceError:
                    logging.error("Requested invalid service: %s" % service)
                    error = True
                    continue
                except fritzconnection.fritzconnection.ActionError:
                    logging.error("Requested invalid action: %s" % action)
                    error = True
                    continue

                for instance in content['value_instances']:

                    rewrite_name = None

                    if ':' in instance:
                        instance, rewrite_name = instance.split(':')
                        instance = instance.strip()
                        rewrite_name = rewrite_name.strip()

                    # only keep desired result key
                    if instance in this_result:
                        result.update({rewrite_name if rewrite_name is not None else instance: this_result[instance]})
            else:
                try:
                    result.update(fc.call_action(service, action))
                except fritzconnection.fritzconnection.ServiceError:
                    logging.error("Requested invalid service: %s" % service)
                    error = True
                    continue
                except fritzconnection.fritzconnection.ActionError:
                    logging.error("Requested invalid action: %s" % action)
                    error = True
                    continue

    if error is True:
        logging.error("Encountered errors while requesting data. Exit")
        exit(1)

    return sanitize_fb_return_data(result)


def read_config(filename):

    config = None

    # check if config file exists
    if not os.path.isfile(filename):
        logging.error("config file \"%s\" not found" % filename)
        exit(1)

    # check if config file is readable
    if not os.access(filename, os.R_OK):
        logging.error("config file \"%s\" not readable" % filename)
        exit(1)

    try:
        config = configparser.ConfigParser()
        config.read(filename)
    except configparser.Error as e:
        logging.error("Config Error: %s", str(e))
        exit(1)

    logging.info("Done parsing config file")

    return config


def check_db_status(db_handler, db_name):

    dblist = None

    try:
        dblist = db_handler.get_list_database()
    except Exception as e:
        logging.error('Problem connecting to database: %s', e)
        exit(1)

    if db_name not in [db['name'] for db in dblist]:

        logging.info('Database <%s> not found, trying to create it' % db_name)

        try:
            db_handler.create_database(db_name)
        except Exception as e:
            logging.error('Problem creating database: %s', e)
            exit(1)
    else:
        logging.debug('Influx Database <%s> exists' % db_name)

    logging.info("Connection to InfluxDB established and database present")

    return


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
    signal.signal(signal.SIGINT, shutdown)

    # parse command line arguments
    args = parse_args()

    # set logging
    log_level = logging.DEBUG if args.verbose is True else default_log_level

    if args.daemon:
        # omit time stamp if run in daemon mode
        logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')
    else:
        logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s: %(message)s')

    # read config from ini file
    config = read_config(args.config_file)

    # set up influxdb handler
    influxdb_client = None
    try:
        influxdb_client = influxdb.InfluxDBClient(
            config.get('influxdb', 'host'),
            config.getint('influxdb', 'port'),
            config.get('influxdb', 'username'),
            config.get('influxdb', 'password'),
            config.get('influxdb', 'database'),
            config.get('influxdb', 'ssl'),
            config.get('influxdb', 'verify_ssl'),
        )
        # test more config options
        _ = config.get('influxdb', 'measurement_name')
    except configparser.Error as e:
        logging.error("Config Error: %s", str(e))
        exit(1)
    except ValueError as e:
        logging.error("Config Error: %s", str(e))
        exit(1)

    # check influx db status
    check_db_status(influxdb_client, config.get('influxdb', 'database'))

    # create unauthenticated FB client handler
    fritz_client_unauth = None
    try:
        fritz_client_unauth = fritzconnection.FritzConnection(
            address=config.get('fritzbox', 'host'),
            port=config.get('fritzbox', 'port'),
        )
    except configparser.Error as e:
        logging.error("Config Error: %s", str(e))
        exit(1)

    # test connection
    if fritz_client_unauth.modelname is None:
        logging.error("Failed to connect to FritzBox '%s'" % config.get('fritzbox', 'host'))
        exit(1)

    # create authenticated FB client handler
    fritz_client_auth = None
    try:
        fritz_client_auth = fritzconnection.FritzConnection(
            address=config.get('fritzbox', 'host'),
            port=config.get('fritzbox', 'port'),
            user=config.get('fritzbox', 'username'),
            password=config.get('fritzbox', 'password')
        )
    except configparser.Error as e:
        logging.error("Config Error: %s", str(e))
        exit(1)

    # test auth connection
    try:
        fritz_client_auth.call_action("DeviceInfo", "GetInfo")
    except fritzconnection.fritzconnection.FritzConnectionException:
        logging.error("Failed to connect to FritzBox '%s' using credentials. Check username and password!" %
                      config.get('fritzbox', 'host'))
        exit(1)

    logging.info("Successfully connected to FritzBox")

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

        logging.debug("writing data to InfluxDB")

        # noinspection PyBroadException
        try:
            influxdb_client.write_points([data], time_precision="ms")
        except Exception:
            logging.error("Failed to write to InfluxDB %s" % config.get('influxdb', 'host'))

        # just sleep for 10 seconds
        time.sleep(10)


if __name__ == "__main__":
    main()
