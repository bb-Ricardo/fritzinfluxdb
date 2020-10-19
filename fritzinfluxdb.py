#!/usr/bin/env python3

self_description = """
Fritz InfluxDB is a tiny daemon written to fetch data from a fritz box router and
writes it to an InfluxDB instance.
"""

# import standard modules
from argparse import ArgumentParser, RawDescriptionHelpFormatter
import configparser
from datetime import datetime
import json
import logging
import os
import signal
import time
import threading

# import 3rd party modules
import fritzconnection
import influxdb


__version__ = "0.3.1"
__version_date__ = "2020-09-17"
__description__ = "fritzinfluxdb"
__license__ = "MIT"

# default vars
running = True
default_config = os.path.join(os.path.dirname(__file__), 'fritzinfluxdb.ini')
default_log_level = logging.DEBUG
default_log_path = os.path.join(os.path.dirname(__file__), 'fritzinfluxdb.log')

#set logging
logging.basicConfig(filename=default_log_path, level=default_log_level, format="[%(asctime)s][%(threadName)-18s| %(levelname)-8s] %(message)s")


def parse_args():
    """parse command line arguments

    Also add current version and version date to description
    """

    parser = ArgumentParser(
        description=self_description + f"\nVersion: {__version__} ({__version_date__})",
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
    """
    Signal handler which ends the loop
    Parameters
    ----------
    exit_signal: int
        signal value
    frame: unused

    """

    global running
    logging.info(f"Program terminated. Signal {exit_signal}")
    running = False


def sanitize_fb_return_data(results):
    """
    Sometimes integers are returned as string
    try to sanitize this a bit

    Parameters
    ----------
    results: dict
        dict of results from fritzconnection call

    Returns
    -------
    dict: sanitized version of results
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


def query_services(fc, services):
    """
    Query all services from a Fritzbox which are defined in config

    Parameters
    ----------
    fc: fritzconnection.FritzConnection
        initialized fritzconnection handler
    services: dict

    Returns
    -------
    dict: dict of requested and sanitized value_instances
    """

    result = dict()
    error = False

    def _fb_call_action(service_called, action_called):
        """
        Perform actual Fritzbox request

        Parameters
        ----------
        service_called: str
            name of requested service
        action_called: str
            name of requested action
        box: str
            name of the fritzbox

        Returns
        -------
        dict: result from called action or None if an error occurred
        """

        call_result = None
        logging.debug(f"Requesting {service_called} : {action_called}")
        try:
            call_result = fc.call_action(service_called, action_called)
        except fritzconnection.core.exceptions.FritzServiceError:
            logging.error(f"Requested invalid service: {service_called}")
        except fritzconnection.core.exceptions.FritzActionError:
            logging.error(f"Requested invalid action '{action_called}' for service: {service_called}")

        if call_result is not None:
            logging.debug("Request returned successfully")

            for key, value in call_result.items():
                logging.debug(f"Response: {key} = {value}")

        return call_result

    for service, content in services.items():

        for action in content['actions']:

            if 'value_instances' in content:

                this_result = _fb_call_action(service, action)

                if this_result is None:
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

                this_result = _fb_call_action(service, action)

                if this_result is None:
                    error = True
                    continue

                result.update(this_result)

    if error is True:
        logging.error("Encountered problems while requesting data. Data might be incomplete.")

    return sanitize_fb_return_data(result)


def read_config(filename):
    """
    Read config ini file and return configparser object

    Parameters
    ----------
    filename: str
        path of ini file to parse

    Returns
    -------
    configparser.ConfigParser(): configparser object
    """

    config = None

    # check if config file exists
    if not os.path.isfile(filename):
        logging.error(f'Config file "{filename}" not found')
        exit(1)

    # check if config file is readable
    if not os.access(filename, os.R_OK):
        logging.error(f'Config file "{filename}" not readable')
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
    """
    Check if InfluxDB handler has access to a database.
    If it doesn't exist try to create it.

    Parameters
    ----------
    db_handler: influxdb.InfluxDBClient
        InfluxDB handler object

    db_name: str
        Name of DB to check
    """

    try:
        dblist = db_handler.get_list_database()
    except Exception as e:
        logging.error('Problem connecting to database: %s', str(e))
        return

    if db_name not in [db['name'] for db in dblist]:

        logging.info(f'Database <{db_name}> not found, trying to create it')

        try:
            db_handler.create_database(db_name)
        except Exception as e:
            logging.error('Problem creating database: %s', str(e))
            return
    else:
        logging.debug(f'Influx Database <{db_name}> exists')

    logging.info("Connection to InfluxDB established and database present")

    return


def get_services(config, section_name_prefix):
    """
    Parse all sections matching the prefix to a dict which is used to request services and actions.

    Parameters
    ----------
    config: configparser.ConfigParser
        configparser object with current config
    section_name_prefix: str
        prefix of section names to parse

    Returns
    -------
    dict: a dict of all services and values instances which match the prefix
    """

    this_sections = [s for s in config.sections() if s.startswith(section_name_prefix)]
    this_services = {}
    for s in this_sections:
        this_services.update({config.get(s, 'service'): {'actions': config.get(s, 'actions').split("\n")}})
        if config.has_option(s, 'value_instances'):
            this_services[config.get(s, 'service')].update(
                {'value_instances': config.get(s, 'value_instances').split("\n")})

    return this_services


def thread_function(box, influxdb_client, config):
    logging.info("starting")
    # create authenticated FB client handler
    fritz_client_auth = None
    request_interval = 10
    conn = True
    while conn == True:
        try:
            fritz_client_auth = fritzconnection.FritzConnection(
                address=config.get(box, 'host', fallback='192.168.178.1'),
                port=config.getint(box, 'port', fallback=49000),
                user=config.get(box, 'username'),
                password=config.get(box, 'password'),
                timeout=config.getint(box, 'timeout', fallback=5),
                use_tls=config.getboolean(box, 'ssl', fallback=False)
            )

            request_interval = config.getint(box, 'interval', fallback=10)
            conn = False

        except configparser.Error as e:
            logging.error("Config Error: %s" % str(e))
            conn = False
            exit(1)
        except BaseException as e:
            logging.error("Failed to connect '%s' --> Retrying" % str(e))
            time.sleep(10)
            

    # test connection
    try:
        fritz_client_auth.call_action("DeviceInfo", "GetInfo")
    except fritzconnection.core.exceptions.FritzConnectionException as e:
        if "401" in str(e):
            logging.error("Failed to connect to FritzBox using credentials. Check username and password!")
        else:
            logging.error("%s" % str(e))

        exit(1)

    logging.info("Successfully connected")

    # read services from config file
    services_to_query = get_services(config, "service")

    logging.info("Starting main loop")

    while running:
        logging.debug("Starting FritzBox requests")

        start = int(datetime.utcnow().timestamp() * 1000)

        # query data
        try: 
            query_data = query_services(fritz_client_auth, services_to_query)
        except:
            query_data = ""
        data = {
            "measurement": config.get('influxdb', 'measurement_name'),
            "tags": {
                "host": box
            },
            "time": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            "fields": query_data
        }

        logging.debug("Writing data to InfluxDB")
        logging.debug("InfluxDB - time: %s" % data.get("time"))
        for k, v in data.get("fields").items():
            logging.debug(f"InfluxDB - field: {k} = {v}")

        # noinspection PyBroadException
        try:
            influxdb_client.write_points([data], time_precision="ms")
        except Exception as e:
            logging.error("Failed to write to InfluxDB <%s>: %s" % str(e))

        duration = int(datetime.utcnow().timestamp() * 1000) - start

        logging.debug("Duration of requesting Fritzbox and sending data to InfluxDB: %0.3fs" % (duration / 1000))

        if duration + 1000 >= (request_interval * 1000):
            logging.warning(f"Request interval of {request_interval} seconds might be to short considering last "
                            "duration for all requests was %0.3f seconds" % (duration / 1000))

        # just sleep for interval seconds - last run duration
        for _ in range(0, int(((request_interval * 1000) - duration) / 100)):
            if running is False:
                break
            time.sleep(0.0965)


def main():
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    # parse command line arguments
    args = parse_args()

    # read config from ini file
    config = read_config(args.config_file)

    # set up influxdb handler
    influxdb_client = None
    try:
        influxdb_client = influxdb.InfluxDBClient(
            config.get('influxdb', 'host'),
            config.getint('influxdb', 'port', fallback=8086),
            config.get('influxdb', 'username'),
            config.get('influxdb', 'password'),
            config.get('influxdb', 'database'),
            config.getboolean('influxdb', 'ssl', fallback=False),
            config.getboolean('influxdb', 'verify_ssl', fallback=False)
        )
        # test more config options and see if they are present
        _ = config.get('influxdb', 'measurement_name')
        _ = config.get('influxdb', 'boxes')
    except configparser.Error as e:
        logging.error("Config Error: %s", str(e))
        exit(1)
    except ValueError as e:
        logging.error("Config Error: %s", str(e))
        exit(1)

    # check influx db status
    check_db_status(influxdb_client, config.get('influxdb', 'database'))

    # creating thread list
    threads = list()

    # run thread for each fritzbox
    for box in json.loads(config.get('influxdb', 'boxes')):
        logging.info("Main  : create and start thread %s" % box)
        x = threading.Thread(target=thread_function, args=(box, influxdb_client, config))
        threads.append(x)
        x.start()


if __name__ == "__main__":
    main()
