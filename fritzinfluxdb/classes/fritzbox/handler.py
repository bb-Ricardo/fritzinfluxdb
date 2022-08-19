# -*- coding: utf-8 -*-
#
#  fritzinfluxdb.py
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see file LICENSE.txt included in this
#  repository or visit: <https://opensource.org/licenses/MIT>.

import asyncio
import urllib3
import requests
from xml.etree.ElementTree import fromstring
import hashlib
import json

# import 3rd party modules
from fritzconnection import FritzConnection
from fritzconnection.core.exceptions import FritzConnectionException, FritzServiceError, FritzActionError

from fritzinfluxdb.classes.fritzbox.config import FritzBoxConfig
from fritzinfluxdb.log import get_logger
from fritzinfluxdb.classes.fritzbox.service_handler import FritzBoxTR069Service, FritzBoxLuaService
from fritzinfluxdb.classes.fritzbox.services_tr069 import fritzbox_services as tr069_services
from fritzinfluxdb.classes.fritzbox.services_lua import fritzbox_services as lua_services
from fritzinfluxdb.classes.common import FritzMeasurement
from fritzinfluxdb.common import grab

log = get_logger()


class FritzBoxHandlerBase:
    """
        base class to provide common methods to both FritzBox handler classes
    """

    config = None
    session = None
    init_successful = False
    services = None
    discovery_done = False

    def __init__(self, config):
        if isinstance(config, FritzBoxConfig):
            self.config = config
        else:
            self.config = FritzBoxConfig(config)

        self.init_successful = False
        self.services = list()
        self.current_result_list = list()

        self.version = None

    def add_services(self, class_name, service_definition):
        """
        Adds services from config to handler

        Parameters
        ----------
        class_name: FritzBoxTR069Service, FritzBoxLuaService
            the fritzbox service class
        service_definition: list
            list of service definitions
        """

        for fritzbox_service in service_definition:
            new_service = class_name(fritzbox_service)

            # adjust request interval if necessary
            if self.config.request_interval > new_service.interval:
                new_service.interval = self.config.request_interval

            self.services.append(new_service)

    def query_service_data(self, _):
        # dummy service to make IDE happy
        pass

    async def task_loop(self, queue):
        """
        common task loop which is called in fritzinfluxdb.py

        Parameters
        ----------
        queue: asyncio.Queue
            the result queue object to write measurements to so the influx handler can pick them up

        """
        while True:

            self.current_result_list = list()
            for service in self.services:
                self.query_service_data(service)

            for result in self.current_result_list:
                log.debug(result)
                await queue.put(result)

            await asyncio.sleep(1)

            # first discovery run is done
            self.discovery_done = True


class FritzBoxHandler(FritzBoxHandlerBase):

    name = "FritzBox TR-069"

    def __init__(self, config):

        super().__init__(config)

        # parse services from fritzbox/services_tr069.py
        self.add_services(FritzBoxTR069Service, tr069_services)

    def connect(self):

        if self.init_successful is True:
            return

        log.debug(f"Initiating new {self.name} session")

        try:
            self.session = FritzConnection(
                address=self.config.hostname,
                port=self.config.port,
                user=self.config.username,
                password=self.config.password,
                timeout=(self.config.connect_timeout, self.config.connect_timeout * 4),
                use_tls=self.config.tls_enabled
            )

            self.version = self.session.system_version

        except BaseException as e:
            log.error(f"Failed to connect to FritzBox via TR-069 '{e}'")
            return

        # test connection
        try:
            device_info = self.session.call_action("DeviceInfo", "GetInfo")
        except FritzConnectionException as e:
            if "401" in str(e):
                log.error(f"Failed to connect to {self.name} '{self.config.hostname}' using credentials. "
                          "Check username and password!")
            else:
                log.error(f"Failed to connect to {self.name} '{self.config.hostname}': {e}")

            return
        except BaseException as e:
            log.error(f"Failed to connect to {self.name} '{self.config.hostname}': {e}")
            return

        if isinstance(device_info, dict):
            self.config.model = device_info.get("NewModelName")
            self.config.fw_version = device_info.get("NewSoftwareVersion")

        log.info(f"Successfully established {self.name} session")

        self.init_successful = True

    def close(self):
        self.session.session.close()
        if self.init_successful is True:
            log.info(f"Closed {self.name} connection")

    def query_service_data(self, service):

        if not isinstance(service, FritzBoxTR069Service):
            log.error("Query service must be of type 'FritzBoxTR069Service'")
            return

        if self.discovery_done is True and service.should_be_requested() is False:
            return

        # Request every action
        for action in service.actions:

            if service.available is False:
                break

            if self.discovery_done is True and action.available is False:
                log.debug(f"Skipping disabled service action: {service.name} - {action.name}")
                continue

            # add parameters
            try:
                call_result = self.session.call_action(service.name, action.name, **action.params)
            except FritzServiceError:
                log.info(f"Requested invalid service: {service.name}")
                if self.discovery_done is False:
                    log.info(f"Querying service '{service.name}' will be disabled")
                    service.available = False
                continue
            except FritzActionError:
                log.info(f"Requested invalid action '{action.name}' for service: {service.name}")
                if self.discovery_done is False:
                    log.info(f"Querying action '{action.name}' will be disabled")
                    action.available = False
                continue
            except FritzConnectionException as e:
                if "401" in str(e):
                    log.error(f"Failed to connect to {self.name} '{self.config.hostname}' using credentials. "
                              "Check username and password!")
                else:
                    log.error(f"Failed to connect to {self.name} '{self.config.hostname}': {e}")
                continue
            except Exception as e:
                log.error(f"Unable to request {self.name} data: {e}")
                continue

            if call_result is None:
                continue

            log.debug(f"Request {self.name} service '{service.name}' returned successfully: "
                      f"{action.name} ({action.params})")

            # set time stamp of this query
            service.set_last_query_now()

            for key, value in call_result.items():
                log.debug(f"{self.name} result: {key} = {value}")
                metric_name = service.value_instances.get(key)

                if metric_name is not None:
                    self.current_result_list.append(
                        FritzMeasurement(metric_name, value, box_tag=self.config.box_tag)
                    )

        if self.discovery_done is False:
            if True not in [x.available for x in service.actions]:
                log.info(f"All actions for service '{service.name}' are unavailable. Disabling service.")
                service.available = False

        return


class FritzBoxLuaHandler(FritzBoxHandlerBase):

    name = "FritzBox Lua"

    def __init__(self, config):
        super().__init__(config)

        self.url = None
        self.sid = None

        # disable TLS insecure warnings if user explicitly switched off validation
        if bool(self.config.verify_tls) is False:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        proto = "http"
        if self.config.tls_enabled is True:
            proto = "https"

        self.url = f"{proto}://{self.config.hostname}"

        self.session = requests.Session()
        self.session.verify = self.config.verify_tls

        # parse services from fritzbox/services_lua.py
        self.add_services(FritzBoxLuaService, lua_services)

    def connect(self):

        if self.sid is not None:
            return

        login_url = f"{self.url}/login_sid.lua"

        log.debug(f"Initiating new {self.name} session")

        # perform login
        try:
            response = self.session.get(login_url, timeout=(self.config.connect_timeout, self.config.connect_timeout*4))
        except Exception as e:
            log.error(f"Unable to create {self.name} session: {e}")
            return

        try:
            dom = fromstring(response.content)
            sid = dom.findtext('./SID')
            challenge = dom.findtext('./Challenge')
        except Exception as e:
            log.error(f"Unable to parse {self.name} login response: {e} {response.content}")
            return

        if sid != "0000000000000000":
            log.error(f"Unexpected {self.name} session id: {sid}")
            return

        md5 = hashlib.md5()
        md5.update(challenge.encode('utf-16le'))
        md5.update('-'.encode('utf-16le'))
        md5.update(self.config.password.encode('utf-16le'))

        login_params = {
            "username": self.config.username,
            "response": challenge + '-' + md5.hexdigest()
        }

        try:
            response = self.session.get(login_url, timeout=self.config.connect_timeout, params=login_params)
            sid = fromstring(response.content).findtext('./SID')
        except Exception as e:
            log.error(f"Unable to parse {self.name} login response: {e} {response.content}")
            return

        if sid == "0000000000000000":
            log.error(f"Failed to connect to {self.name} '{self.config.hostname}' using credentials. "
                      "Check username and password!")
            return

        log.info(f"Successfully established {self.name} session")

        self.sid = sid
        self.init_successful = True

    def request(self, page, additional_params):

        result = None

        if self.sid is None:
            self.connect()

        params = {
            "page": page,
            "lang": "de",
            "sid": self.sid
        }

        if isinstance(additional_params, dict):
            params = {**params, **additional_params}

        data_url = f"{self.url}/data.lua"
        try:
            response = self.session.post(data_url, timeout=self.config.connect_timeout, data=params)
        except Exception as e:
            log.error(f"Unable to perform request to '{data_url}': {e}")
            return

        try:
            result = response.json()
        except json.decoder.JSONDecodeError:
            pass

        if response.status_code == 200 and result is not None:
            log.debug(f"{self.name} request successful")

        else:
            log.error(f"{self.name} returned: {response.status_code} : {response.reason}")
            log.error(f"{self.name} returned body: {result}")

            # invalidate session
            if response.status_code in [303, 403]:
                self.sid = None

        return result

    def close(self):
        self.session.close()
        if self.init_successful is True:
            log.info(f"Closed {self.name} connection")

    def extract_value(self, service, data, metric_name, metric_params):

        # read config
        data_path = metric_params.get("data_path")
        data_type = metric_params.get("type")
        data_next = metric_params.get("next")
        data_tags = metric_params.get("tags")
        value_function = metric_params.get("value_function")
        tags_function = metric_params.get("tags_function")                      # needs to return a dict
        timestamp_function = metric_params.get("timestamp_function")            # needs to return a datetime
        exclude_filter_function = metric_params.get("exclude_filter_function")  # needs to return a bool

        # define defaults
        metric_value = None
        timestamp = None
        metric_tags = dict()

        # noinspection PyBroadException
        try:
            if exclude_filter_function(data) is True:
                return
        except Exception:
            pass

        if data_path is not None and value_function is not None:
            log.error("Attributes 'data_path' and 'value_function' cant be defined for the same entry"
                      f"at the same time: {metric_params}")
            return

        # first we try to use the value_function
        if value_function is not None:
            # noinspection PyBroadException
            try:
                metric_value = value_function(data)
            except Exception:
                pass

        elif data_path is not None:
            metric_value = grab(data, data_path)

        # try to add tags
        if isinstance(data_tags, dict):
            metric_tags = data_tags

        # noinspection PyBroadException
        try:
            metric_tags = {**metric_tags, **tags_function(data)}
        except Exception:
            pass

        # noinspection PyBroadException
        try:
            timestamp = timestamp_function(data)

            # make timestamp time zone aware if time zone is missing
            if timestamp.tzinfo is None or timestamp.tzinfo.utcoffset(timestamp) is None:
                timestamp = self.config.timezone.localize(timestamp)

        except Exception:
            pass

        if metric_value is None:
            log.error(f"Unable to extract '{data_path}' form '{data}', got '{type(metric_value)}'")
            return

        if data_type in [int, float, bool, str]:
            try:
                metric_value = data_type(metric_value)
            except Exception as e:
                log.error(f"Unable to convert {self.name} value '{metric_value}' to '{data_type}': {e}")

            metric = FritzMeasurement(metric_name, metric_value, data_type=data_type, box_tag=self.config.box_tag,
                                      additional_tags=metric_tags, timestamp=timestamp)

            # check if measurement is tracked and already reported
            if service.skip_tracked_measurement(metric) is True:
                return

            # track measurement (if configured)
            service.add_tracked_measurement(metric)

            self.current_result_list.append(metric)
            return

        if type(metric_value) != data_type:
            log.error(f"FritzBox metric type '{data_type}' does not match data: {type(metric_value)}")
            return

        if data_type == list and data_next is not None:
            for next_metric_value in metric_value:
                self.extract_value(service, next_metric_value, metric_name, data_next)

            return

        if data_type == dict and data_next is not None:
            for next_metric_value in metric_value.values():
                self.extract_value(service, next_metric_value, metric_name, data_next)

            return

        log.error(f"Unknown metric '{data_path}' form '{data}', with type '{type(metric_value)}' "
                  f"and defined type '{data_type}'")

    def query_service_data(self, service):

        if not isinstance(service, FritzBoxLuaService):
            log.error("Query service must be of type 'FritzBoxLuaService'")
            return

        if self.discovery_done is True and service.should_be_requested() is False:
            return

        # request data
        result = self.request(service.page, additional_params=service.params)

        if result is None or result.get("pid") != service.page:
            message_handler = log.info
            message_text = f"Unable to request {self.name} service '{service.name}'"
            if result is None:
                message_handler = log.error
                message_text += ", no data returned"
            elif self.discovery_done is True:
                message_handler = log.error

            message_handler(message_text)

            if self.discovery_done is False:
                log.info(f"{self.name} service '{service.name}' will be disabled.")
                service.available = False
            return

        log.debug(f"Request {self.name} service '{service.name}' returned successfully")

        # set time stamp of this query
        service.set_last_query_now()

        # Request every param
        for metric_name, metric_params in service.value_instances.items():
            self.extract_value(service, result, metric_name, metric_params)

        return
