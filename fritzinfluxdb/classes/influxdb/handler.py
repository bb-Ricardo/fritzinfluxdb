# -*- coding: utf-8 -*-
#
#  fritzinfluxdb.py
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see file LICENSE.txt included in this
#  repository or visit: <https://opensource.org/licenses/MIT>.

import asyncio

# InfluxDB version 1.x client
import influxdb
# InfluxDB version 2.x client
from influxdb_client import InfluxDBClient, BucketRetentionRules
from influxdb_client.rest import ApiException
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.domain.write_precision import WritePrecision

from fritzinfluxdb.classes.influxdb.config import InfluxDBConfig
from fritzinfluxdb.log import get_logger
from fritzinfluxdb.classes.common import FritzMeasurement

log = get_logger()


class InfluxHandler:

    config = None
    session_v1 = None
    session_v2 = None
    session_v2_write_api = None

    # default InfluxDB connection timeout
    connection_timeout_v1 = 2
    connection_timeout_v2 = 5

    # default number of days to keep our fritzinfluxdb data in InfluxDB
    bucket_retention_days = 365

    # max size of message buffer before discarding old measurements
    max_measurements_buffer_size = 1_000_000

    # max number of measurements written with each InfluxDB write
    max_measurements_per_write = 1_000

    # keep track if this instance was initiated successfully
    init_successful = False

    # set to true if connection to InfluxDB got lost
    connection_lost = False

    def __init__(self, config):

        self.config = InfluxDBConfig(config)
        self.init_successful = False

        self.buffer = list()

    def connect(self):

        if self.config.version == 1:

            self.session_v1 = influxdb.InfluxDBClient(
                host=self.config.hostname,
                port=self.config.port,
                username=self.config.username,
                password=self.config.password,
                database=self.config.database,
                ssl=self.config.tls_enabled,
                verify_ssl=self.config.verify_tls,
                timeout=self.connection_timeout_v1
            )

            # check influx db status
            self.check_db_status()
        else:

            proto = "http"
            if self.config.tls_enabled:
                proto = "https"

            self.session_v2 = InfluxDBClient(
                url=f"{proto}://{self.config.hostname}:{self.config.port}",
                port=self.config.port,
                token=self.config.token,
                org=self.config.organisation,
                ssl=self.config.tls_enabled,
                verify_ssl=self.config.verify_tls,
                timeout=self.connection_timeout_v2 * 1000,
                debug=False
            )
            self.check_bucket_status()

            self.session_v2_write_api = self.session_v2.write_api(write_options=SYNCHRONOUS)

    def close(self):

        if self.session_v1 is not None:
            self.session_v1.close()
            log.info("Closed InfluxDB session")

        if self.session_v2 is not None:
            self.session_v2.close()
            log.info("Closed InfluxDB session")

    def check_db_status(self):
        """
        Check if InfluxDB handler has access to a database.
        If it doesn't exist try to create it.
        """

        if self.config.version != 1:
            return

        if self.session_v1 is None:
            log.error("Unable to check InfluxDB status. Session not initiated")
            return

        if self.config.database is None:
            log.error("InfluxDB database undefined in config")

        try:
            db_list = self.session_v1.get_list_database()
        except Exception as e:
            log.error(f"Problem connecting to InfluxDB database: {e}")
            return

        if self.config.database not in [db['name'] for db in db_list]:

            log.info(f"Database '{self.config.database}' not found, trying to create it")

            try:
                self.session_v1.create_database(self.config.database)
            except Exception as e:
                log.error(f"Problem creating database: {e}")
                return
        else:
            log.debug(f"InfluxDB database '{self.config.database}' exists")

        log.info("Connection to InfluxDB established and database present")

        self.init_successful = True

    def check_bucket_status(self):

        if self.config.version != 2:
            return

        # get list of buckets and see if the configured bucket exists
        try:
            buckets_api = self.session_v2.buckets_api()
            buckets = buckets_api.find_buckets().buckets
        except ApiException as e:
            log.error(f"Problem reading configured InfluxDB buckets: {e.status}: {e.reason}")
            return
        except Exception as e:
            log.error(f"Problem reading configured InfluxDB buckets: {e}")
            return

        self.config.bucket_data = None
        for bucket in buckets or list():
            if self.config.bucket in [bucket.name, bucket.id]:
                log.debug(f"InfluxDB Bucket '{self.config.bucket}' exists")
                self.config.bucket_data = bucket

        # create new bucket
        if self.config.bucket_data is None:
            log.info(f"InfluxDB bucket '{self.config.bucket}' not found, trying to create it")
            try:
                retention_rules = BucketRetentionRules(type="expire",
                                                       every_seconds=3600 * 24 * self.bucket_retention_days)
                self.config.bucket_data = \
                    buckets_api.create_bucket(bucket_name=self.config.bucket,
                                              retention_rules=retention_rules,
                                              org=self.config.organisation,
                                              description="FritzInfluxDB bucket")
            except Exception as e:
                log.error(f"Problem creating InfluxDB bucket: {e}")
                return

        log.info("Connection to InfluxDB established and bucket is present")

        self.init_successful = True

    def convert_measurement(self, measurement):

        if not isinstance(measurement, FritzMeasurement):
            log.error(f"Measurement needs to be a 'FritzMeasurement' but got '{type(measurement)}'")
            return

        return {
            "measurement": self.config.measurement_name,
            "tags": {"box": measurement.tag},
            "time": measurement.timestamp,
            "fields": {measurement.name: measurement.value}
        }

    async def write_data(self):

        if len(self.buffer) == 0:
            log.debug("InfluxDB data queue: No measurements found in queue")
            return

        local_buffer = self.buffer[0:self.max_measurements_per_write]

        data = [self.convert_measurement(x) for x in local_buffer]

        write_successful = False
        try:
            if self.config.version == 1:
                write_successful = self.session_v1.write_points(data, time_precision="ms")
            elif self.config.version == 2:
                self.session_v2_write_api.write(bucket=self.config.bucket, record=data,
                                                write_precision=WritePrecision.MS)
                write_successful = True
        except Exception as e:
            self.connection_lost = True
            log.error(f"Failed to write to InfluxDB '{self.config.hostname}': {e}")
            return

        if write_successful is True:
            if self.connection_lost is True:
                log.info(f"Connection to influxDB '{self.config.hostname}' restored.")
                log.info(f"Flushing '{len(self.buffer)}' measurements to InfluxDB")

            log.debug(f"Successfully wrote {len(local_buffer)} measurements to InfluxDB")
            self.buffer[:] = [x for x in self.buffer if x not in local_buffer]

            self.connection_lost = False

    async def check_buffer(self):

        length = len(self.buffer)
        max_length = self.max_measurements_buffer_size

        if length > max_length:
            log.warning(f"InfluxDB measurement buffer length '{length}' "
                        f"exceeded the maximum of {max_length} items. "
                        f"Discarding oldest {length - max_length} measurements.")
            self.buffer[:] = self.buffer[0 - max_length:]

    async def parse_queue(self, queue):

        while True:

            # transfer items to instance buffer
            while queue.empty() is False:
                # add measurements to instance buffer
                self.buffer.append(await queue.get())

            # write data from buffer to InfluxDB
            await self.write_data()
            await self.check_buffer()

            log.debug(f"Current InfluxDB measurement buffer length: {len(self.buffer)}")
            await asyncio.sleep(1)

# EOF
