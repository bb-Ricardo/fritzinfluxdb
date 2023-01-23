# -*- coding: utf-8 -*-
#  Copyright (c) 2022 - 2022 Ricardo Bartels. All rights reserved.
#
#  fritzinfluxdb.py
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see file LICENSE.txt included in this
#  repository or visit: <https://opensource.org/licenses/MIT>.

import asyncio
import pytz
from datetime import datetime
from http.client import HTTPConnection
from logging import LogRecord

import requests

# InfluxDB version 1.x client
from influxdb import InfluxDBClient as InfluxDBClientV1
from influxdb.exceptions import InfluxDBClientError
# InfluxDB version 2.x client
from influxdb_client import InfluxDBClient as InfluxDBClientV2, BucketRetentionRules, DBRPCreate, DBRPsService
from influxdb_client.rest import ApiException
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.domain.write_precision import WritePrecision

from fritzinfluxdb.classes.influxdb.config import InfluxDBConfig
from fritzinfluxdb.log import get_logger
from fritzinfluxdb.classes.common import FritzMeasurement

from fritzinfluxdb.classes.fritzbox.config import FritzBoxConfig

log = get_logger()


class InfluxHandler:

    name = "InfluxDB"

    config = None
    session_v1 = None
    session_v2 = None
    session_v2_write_api = None

    # default InfluxDB connection timeout
    connection_timeout_v1 = 2
    connection_timeout_v2 = 5

    # max size of message buffer before discarding old measurements
    max_measurements_buffer_size = 1_000_000

    # max number of measurements written with each InfluxDB write
    max_measurements_per_write = 1_000

    # percentage of filled buffer to start issue warnings
    max_measurements_buffer_warning = 80

    # the number of seconds to retry first unsuccessful write.
    # The next retry interval is doubled and so on
    retry_interval = 5

    # max interval between write retries
    max_retry_interval = 120

    # keep track if this instance was initiated successfully
    init_successful = False

    # set to true if connection to InfluxDB got lost
    connection_lost = False

    # keep track if InfluxDB refuses to write data which is out of range
    out_of_retention_period_range = False

    def __init__(self, config, user_agent=None):

        self.config = InfluxDBConfig(config)
        self.version = str(self.config.version)
        self.init_successful = False

        self.buffer = list()

        self.current_retry_interval = self.retry_interval
        self.last_write_retry = None
        self.session_v1_requests_session = requests.Session()
        self.current_max_measurements_buffer_warning = self.max_measurements_buffer_warning
        self.current_measurements_per_write = self.max_measurements_per_write

        if self.config.version == 1:

            self.session_v1 = InfluxDBClientV1(
                host=self.config.hostname,
                port=self.config.port,
                username=self.config.username,
                password=self.config.password,
                database=self.config.database,
                ssl=self.config.tls_enabled,
                verify_ssl=self.config.verify_tls,
                timeout=self.connection_timeout_v1,
                session=self.session_v1_requests_session
            )

        else:

            proto = "http"
            if self.config.tls_enabled:
                proto = "https"

            debug = False
            if HTTPConnection.debuglevel > 0:
                debug = True

            self.session_v2 = InfluxDBClientV2(
                url=f"{proto}://{self.config.hostname}:{self.config.port}",
                port=self.config.port,
                token=self.config.token,
                org=self.config.organisation,
                ssl=self.config.tls_enabled,
                verify_ssl=self.config.verify_tls,
                timeout=self.connection_timeout_v2 * 1000,
                debug=debug
            )

        if user_agent is not None:
            if self.session_v1 is not None:
                self.session_v1_requests_session.headers.update({"User-Agent": user_agent})

            if self.session_v2 is not None:
                self.session_v2.api_client.user_agent = user_agent

    def connect(self):

        if self.init_successful is True:
            return

        if self.config.version == 1:

            try:
                self.version = str(self.session_v1.ping())

            except Exception as e:
                log.error(f"Failed to connect to InfluxDB: {e}")
                return

            # check influx db status
            self.check_db_status()

        else:

            try:
                self.version = str(self.session_v2.version().split(",")[0])

            except Exception as e:
                log.error(f"Failed to connect to InfluxDB: {e}")
                return

            # check status on influxdb buckets, if possible
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

        retention_policies = list()
        retention_policies_query_successful = False
        try:
            retention_policies = self.session_v1.get_list_retention_policies(self.config.database)
            retention_policies_query_successful = True
        except Exception as e:
            log.warning(f"Problem querying database retention policies: {e}")

        if retention_policies_query_successful and len(retention_policies) == 0:
            try:
                self.session_v1.create_retention_policy(
                    name=f"fritzinfluxdb-{self.config.data_retention_days}-days",
                    duration=f"{self.config.data_retention_days}d", replication="1",
                    database=self.config.database, shard_duration="24h", default=True
                )
            except Exception as e:
                log.warning(f"Problem creating database retention policy: {e}")

        log.info(f"Connection to InfluxDB {self.version} established and database present")

        self.init_successful = True

    def check_bucket_status(self):

        if self.config.version != 2:
            return

        # get list of buckets and see if the configured bucket exists
        try:
            buckets_api = self.session_v2.buckets_api()
            buckets = buckets_api.find_buckets().buckets
            dbrp_api = DBRPsService(api_client=self.session_v2.api_client)
        except ApiException as e:
            log.error(f"Problem reading configured InfluxDB buckets: {e.status}: {e.reason}")
            return
        except Exception as e:
            log.error(f"Problem reading configured InfluxDB buckets: {e}")
            return

        if buckets is None or len(buckets) == 0:
            log.debug("Unable to read existing buckets. Assuming this is a token with "
                      "insufficient permissions to perform this action. Assuming the configured bucket is present.")

            self.init_successful = True
            log.info("Connection to InfluxDB 2 established")
            return

        bucket_data = None
        for bucket in buckets or list():
            if self.config.bucket in [bucket.name, bucket.id]:
                log.debug(f"InfluxDB bucket '{self.config.bucket}' exists")
                bucket_data = bucket

        # create new bucket
        if bucket_data is None:
            log.info(f"InfluxDB bucket '{self.config.bucket}' not found, trying to create it")
            try:
                retention_rules = BucketRetentionRules(type="expire",
                                                       every_seconds=3600 * 24 * self.config.data_retention_days,
                                                       shard_group_duration_seconds=3600 * 24)

                bucket_data = buckets_api.create_bucket(bucket_name=self.config.bucket,
                                                        retention_rules=retention_rules,
                                                        org=self.config.organisation,
                                                        description="FritzInfluxDB bucket")

            except Exception as e:
                log.error(f"Problem creating InfluxDB bucket: {e}")
                return

            log.info(f"Successfully create InfluxDB bucket '{self.config.bucket}'")

        # create new bucket
        if bucket_data is not None:
            log.debug(f"InfluxDB bucket '{self.config.bucket}' present, checking database name mapping")
            try:
                bucket_dbrp_data = dbrp_api.get_dbr_ps(bucket_id=bucket_data.id, org=self.config.organisation)
            except Exception as e:
                log.error(f"Problem requesting InfluxDB DBRP data: {e}")
                return

            create_retention_policy = False
            if "1year" not in [x.retention_policy for x in bucket_dbrp_data.content]:
                create_retention_policy = True

            if len(bucket_dbrp_data.content) == 0:
                create_retention_policy = True

            if create_retention_policy is False:
                log.debug(f"InfluxDB bucket '{self.config.bucket}' has a database mapping retention policy: "
                          f"{bucket_dbrp_data.content[0].retention_policy}")
            else:
                try:
                    dbrp_api.post_dbrp(DBRPCreate(
                        org=self.config.organisation,
                        bucket_id=bucket_data.id,
                        database=bucket_data.name,
                        retention_policy="1year",
                        default=True
                    ))
                except Exception as e:
                    log.error(f"Problem creating InfluxDB DBRP data: {e}")
                    return

                log.info(f"Successfully create InfluxDB database mapping '{self.config.bucket}'")

        log.info(f"Connection to InfluxDB {self.version} established and bucket is present")

        self.init_successful = True

    def convert_measurement(self, measurement):

        if not isinstance(measurement, FritzMeasurement):
            log.error(f"Measurement needs to be a 'FritzMeasurement' but got '{type(measurement)}'")
            return

        return {
            "measurement": self.config.measurement_name,
            "tags": measurement.tags,
            "time": measurement.timestamp,
            "fields": {measurement.name: measurement.value}
        }

    def permitted_to_write_data(self):

        # permit writing if no last write retry is known
        if self.last_write_retry is None:
            return True

        # limit max retry seconds
        if self.current_retry_interval > self.max_retry_interval:
            self.current_retry_interval = self.max_retry_interval

        # check if the next retry is permitted
        if (datetime.now(pytz.utc)-self.last_write_retry).total_seconds() >= self.current_retry_interval:
            return True

        return False

    async def write_data(self):

        if self.permitted_to_write_data() is False:
            return

        if len(self.buffer) == 0:
            log.debug("InfluxDB data queue: No measurements found in queue")
            return

        if self.out_of_retention_period_range is True:

            # sort measurements to write out all the newest measurements first
            # which probably won't hit the retention period boundary
            self.buffer = sorted(self.buffer, key=lambda m: m.timestamp, reverse=True)

        # only use max amount of measurements to send to InfluxDB
        log.debug(f"Trying to write a maximum of '{self.current_measurements_per_write}' measurements to InfluxDB")
        local_buffer = self.buffer[0:self.current_measurements_per_write]

        # convert FritzMeasurement to list of dicts
        data = [self.convert_measurement(x) for x in local_buffer]

        write_successful = False
        self.last_write_retry = datetime.now(pytz.utc)
        try:
            if self.config.version == 1:
                write_successful = self.session_v1.write_points(data, time_precision="u")
            elif self.config.version == 2:
                self.session_v2_write_api.write(bucket=self.config.bucket, record=data,
                                                write_precision=WritePrecision.US)
                write_successful = True
        except (ApiException, InfluxDBClientError) as e:

            exception_message = getattr(e, "message", "")
            http_code = 0
            if isinstance(e, ApiException):
                http_code = e.status
            if isinstance(e, InfluxDBClientError):
                http_code = e.code

            if "points beyond retention policy" in f"{exception_message}":

                log.debug("InfluxDB refused to write data as there seems to be measurements "
                          "which are older then the defined retention period")

                self.out_of_retention_period_range = True
                self.current_retry_interval = 0

                # get timestamp of measurement which is just out of range
                if self.current_measurements_per_write <= 1 and len(self.buffer) > 0:
                    newest_measurement = self.buffer[0]
                    num_purged = len([x for x in self.buffer if x.timestamp <= newest_measurement.timestamp])
                    log.info(f"Purging '{num_purged}' measurements which are older ({newest_measurement.timestamp}) "
                             f"then the InfluxDB configured retention period")
                    self.buffer[:] = [x for x in self.buffer if x.timestamp > newest_measurement.timestamp]
                else:
                    self.set_num_current_measurements_to_write(int(self.current_measurements_per_write/2))
            else:
                log.error(f"Failed to write to InfluxDB '{self.config.hostname}': {http_code}: {exception_message}")

        except Exception as e:
            self.connection_lost = True
            log.error(f"Failed to write to InfluxDB '{self.config.hostname}': {e}")

        if len(self.buffer) == 0:
            self.out_of_retention_period_range = False
            self.current_measurements_per_write = self.max_measurements_per_write

        if write_successful is True:
            if self.connection_lost is True:
                log.info(f"Connection to influxDB '{self.config.hostname}' restored.")
                log.info(f"Flushing '{len(self.buffer)}' measurements to InfluxDB")

            log.debug(f"Successfully wrote {len(local_buffer)} measurements to InfluxDB")
            self.buffer[:] = [x for x in self.buffer if x not in local_buffer]

            self.connection_lost = False
            self.last_write_retry = None
            self.current_retry_interval = self.retry_interval

            self.out_of_retention_period_range = False
            self.set_num_current_measurements_to_write(self.current_measurements_per_write * 2)

        else:
            if self.connection_lost is True:
                self.current_retry_interval *= 2

    def set_num_current_measurements_to_write(self, num_measurements: int):

        if not isinstance(num_measurements, int):
            return

        if num_measurements < 1:
            self.current_measurements_per_write = 1
        elif num_measurements >= self.max_measurements_per_write:
            self.current_measurements_per_write = self.max_measurements_per_write
        else:
            self.current_measurements_per_write = num_measurements

    async def check_buffer(self):

        length = len(self.buffer)
        max_length = self.max_measurements_buffer_size

        percent_buffer_usage = 100 / max_length * length

        buffer_warning_message = f"InfluxDB measurement buffer currently at {percent_buffer_usage:0.2f}% " \
                                 f"(current {length}/max {max_length}). If buffer is full the oldest " \
                                 f"messages will be discarded."

        if length > max_length:
            log.critical(f"InfluxDB measurement buffer length '{length}' "
                         f"exceeded the maximum of {max_length} items. "
                         f"Discarding oldest {length - max_length} measurements.")
            self.buffer[:] = self.buffer[0 - max_length:]

        elif percent_buffer_usage >= self.current_max_measurements_buffer_warning:
            log.warning(buffer_warning_message)
            self.current_max_measurements_buffer_warning += 5
        elif percent_buffer_usage < self.max_measurements_buffer_warning:
            self.current_max_measurements_buffer_warning = self.max_measurements_buffer_warning

    async def task_loop(self, queue):

        while True:

            # transfer items to instance buffer
            while queue.empty() is False:
                # add measurements to instance buffer
                self.buffer.append(await queue.get())

            # write data from buffer to InfluxDB
            await self.write_data()
            await self.check_buffer()

            log.debug(f"Current InfluxDB measurement buffer length: {len(self.buffer)}")
            if self.out_of_retention_period_range is False:
                await asyncio.sleep(1)


class InfluxLogAndConfigWriter:

    name = "InfluxLogAndConfigWriter"

    config = None

    # InfluxDB measurement name
    log_measurement_name = "log_entry"

    # log type of records for fritzinfluxdb instances
    log_record_type = "FritzInfluxDB"

    # measurement name of timezone setting record
    timezone_measurement_name = "fritzinfluxdb_setting_timezone"

    # The log queue to read the log records from
    log_queue = None

    # interval in which to write the timezone setting to InfluxDB
    timezone_setting_write_interval = 60 * 60 * 12  # every twelve hours

    # keep track if this instance was initiated successfully
    init_successful = False

    def __init__(self, config: FritzBoxConfig, log_queue: asyncio.Queue):
        """
        Handler to read log records from 'log_queue', format them to InfluxDB measurements
        and writers them to the output queue.
        Also writes the config option "timezone" to InfluxDB.

        Parameters
        ----------
        config: FritzBoxConfig
            the current FritzBoxConfig
        log_queue: asyncio.Queue
            queue object to read logs from which should be sent to InfluxDB

        Returns
        -------
        handler to use for formatting log entries and write timezone config to InfluxDB
        """

        if not isinstance(config, FritzBoxConfig):
            raise ValueError("param 'config' needs to be a 'FritzBoxConfig' object")

        if not isinstance(log_queue, asyncio.Queue):
            raise ValueError("param 'log_queue' needs to be a 'asyncio.Queue' object")

        self.config = config
        self.log_queue = log_queue

        self.last_timezone_setting_write = None

        self.init_successful = True

    def format_log_record(self, log_record):

        if not isinstance(log_record, LogRecord):
            return None

        log_timestamp = pytz.timezone("UTC").localize(datetime.utcfromtimestamp(log_record.created))

        log_msg = "{levelname}: {message}".format(**log_record.__dict__)

        return FritzMeasurement(self.log_measurement_name, log_msg,
                                box_tag=self.config.box_tag,
                                additional_tags={
                                    "log_type": self.log_record_type
                                },
                                data_type=str,
                                timestamp=log_timestamp,
                                timestamp_precision=WritePrecision.US)

    def get_timezone_setting_measurement(self):

        return FritzMeasurement(self.timezone_measurement_name, self.config.timezone,
                                box_tag=self.config.box_tag,
                                data_type=str)

    def is_time_to_write_timezone_setting(self):

        if self.last_timezone_setting_write is None:
            return True

        if (datetime.now(pytz.utc) - self.last_timezone_setting_write).total_seconds() >= \
                self.timezone_setting_write_interval:
            return True

        return False

    async def task_loop(self, output_queue: asyncio.Queue):

        while True:

            while self.log_queue.empty() is False:
                formatted_log_record = self.format_log_record(await self.log_queue.get())

                if formatted_log_record is None:
                    continue

                log.debug(formatted_log_record)

                await output_queue.put(formatted_log_record)

            # write timezone setting to influx queue
            if self.is_time_to_write_timezone_setting():
                timezone_measurement = self.get_timezone_setting_measurement()
                log.debug(timezone_measurement)
                await output_queue.put(timezone_measurement)
                self.last_timezone_setting_write = datetime.now(pytz.utc)

            await asyncio.sleep(1)

# EOF
