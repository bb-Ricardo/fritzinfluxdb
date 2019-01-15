import os
import sys
import signal
import configparser
import fritzconnection
import influxdb
import time
from datetime import datetime

running = True

def shutdown(signal, frame):
  global running
  running = False

signal.signal(signal.SIGTERM, shutdown)

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

def main(config_filename):
    config = read_config(config_filename)

    influxdb_client = influxdb.InfluxDBClient(
            config.get('influxdb', 'host'),
            config.getint('influxdb', 'port'),
            config.get('influxdb', 'username'),
            config.get('influxdb', 'password'),
            config.get('influxdb', 'database'),
            )
    influxdb_client.create_database(config.get('influxdb', 'database'))

    fritz_client = fritzconnection.FritzConnection(
            address = config.get('fritzbox', 'host'),
            port = config.get('fritzbox', 'port'),
            user = config.get('fritzbox', 'username'),
            password = config.get('fritzbox', 'password')
            )
    if fritz_client.modelname is None:
        raise IOError("fritzinflux: Failed to connect to %s" %
                config.get('fritzbox', 'host'))

    sections = [s for s in config.sections() if s.startswith('service')]
    services = {}
    for s in sections:
        services.update({config.get(s, 'service') : config.get(s, 'actions').split("\n")})

    while running:
        points = query_points(fritz_client, services)
        data = {
                "measurement": config.get('fritzbox', 'measurement_name'),
                "time": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                "fields": points
                }
        influxdb_client.write_points(data, time_precision="ms")
        print(data)
        time.sleep(10)


if __name__ == "__main__":
    main(*sys.argv[1:])

