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

    config = None
    session = None
    init_successful = False
    services = None

    def __init__(self, config):
        if isinstance(config, FritzBoxConfig):
            self.config = config
        else:
            self.config = FritzBoxConfig(config)

        self.init_successful = False
        self.services = list()
        self.current_result_list = list()

    def add_services(self, class_name, service_definition):

        for fritzbox_service in service_definition:
            new_service = class_name(fritzbox_service)

            # adjust request interval if necessary
            if self.config.request_interval > new_service.interval:
                new_service.interval = self.config.request_interval

            self.services.append(new_service)

    def discover_available_services(self):

        for service in self.services:
            self.query_service_data(service, True)

    def query_service_data(self, _, __=None):
        # dummy service to make IDE happy
        pass

    async def query_loop(self, queue):
        while True:

            self.current_result_list = list()
            for service in self.services:
                self.query_service_data(service)

            for result in self.current_result_list:
                log.debug(result)
                await queue.put(result)

            await asyncio.sleep(1)


class FritzBoxHandler(FritzBoxHandlerBase):

    def __init__(self, config):

        super().__init__(config)

        # parse services from fritzbox/services_tr069.py
        self.add_services(FritzBoxTR069Service, tr069_services)

    def connect(self):

        try:
            self.session = FritzConnection(
                address=self.config.hostname,
                port=self.config.port,
                user=self.config.username,
                password=self.config.password,
                timeout=self.config.connect_timeout,
                use_tls=self.config.tls_enabled
            )

        except BaseException as e:
            log.error(f"Failed to connect to FritzBox '{e}'")
            return

        # test connection
        try:
            self.session.call_action("DeviceInfo", "GetInfo")
        except FritzConnectionException as e:
            if "401" in str(e):
                log.error(f"Failed to connect to FritzBox '{self.config.hostname}' using credentials. "
                          "Check username and password!")
            else:
                log.error(f"Failed to connect to FritzBox '{self.config.hostname}': {e}")

            return
        except BaseException as e:
            log.error(f"Failed to connect to FritzBox '{self.config.hostname}': {e}")
            return

        log.info("Successfully connected to FritzBox TR-069 session")
        self.init_successful = True

    def close(self):
        self.session.session.close()
        log.info("Closed FritzBox connection")

    def query_service_data(self, service, discover=False):

        if not isinstance(service, FritzBoxTR069Service):
            log.error("Query service must be of type 'FritzBoxTR069Service'")
            return

        if discover is False and (service.available is False or service.should_service_be_requested() is False):
            return

        # Request every action
        for action in service.actions:

            if discover is False and action.available is False:
                log.debug(f"Skipping disabled action: {action.name}")
                continue

            # add parameters
            try:
                call_result = self.session.call_action(service.name, action.name, **action.params)
            except FritzServiceError:
                log.error(f"Requested invalid service: {service.name}")
                if discover is True:
                    service.available = False
                continue
            except FritzActionError:
                log.error(f"Requested invalid action '{action.name}' for service: {service.name}")
                if discover is True:
                    action.available = False
                continue
            except FritzConnectionException as e:
                if "401" in str(e):
                    log.error(f"Failed to connect to FritzBox '{self.config.hostname}' using credentials. "
                              "Check username and password!")
                else:
                    log.error(f"Failed to connect to FritzBox '{self.config.hostname}': {e}")
                continue
            except Exception as e:
                log.error(f"Unable to request FritzBox data: {e}")
                continue

            if call_result is None:
                continue

            log.debug(f"Request FritzBox service '{service.name}' returned successfully: "
                      f"{action.name} ({action.params})")

            # set time stamp of this query
            service.set_last_query_now()

            for key, value in call_result.items():
                metric_name = service.value_instances.get(key)

                if metric_name is not None:
                    self.current_result_list.append(
                        FritzMeasurement(metric_name, value, self.config.box_tag)
                    )

        return


class FritzboxLuaHandler(FritzBoxHandlerBase):

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

        # perform login
        try:
            response = self.session.get(login_url, timeout=self.config.connect_timeout)
        except Exception as e:
            log.error(f"Unable to create FritzBox Lua session: {e}")
            return

        try:
            dom = fromstring(response.content)
            sid = dom.findtext('./SID')
            challenge = dom.findtext('./Challenge')
        except Exception as e:
            log.error(f"Unable to parse FritzBox login response: {e} {response.content}")
            return

        if sid != "0000000000000000":
            log.error(f"Unexpected FritzBox session id: {sid}")
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
            log.error(f"Unable to parse FritzBox login response: {e} {response.content}")
            return

        if sid == "0000000000000000":
            log.error(f"Failed to connect to FritzBox '{self.config.hostname}' using credentials. "
                      "Check username and password!")
            return

        log.info("Successfully connected to FritzBox Lua session")

        self.sid = sid
        self.init_successful = True

    def request(self, page):

        result = None

        if self.sid is None:
            self.connect()

        params = {
            "page": page,
            "lang": "de",
            "sid": self.sid
        }

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
            log.debug("FritzBox Lua request successful")

        else:
            log.error(f"FritzBox Lua returned: {response.status_code} : {response.reason}")
            log.error(f"FritzBox Lua returned body: {result}")

            # invalidate session
            if response.status_code in [303, 403]:
                self.sid = None

        return result

    def close(self):
        self.session.close()
        log.info("Closed FritzBox Lua connection")

    def extract_value(self, data, metric_name, metric_params):

        data_path = metric_params.get("data_path")
        data_type = metric_params.get("type")
        data_next = metric_params.get("next")
        data_tags = metric_params.get("tags")

        metric_value = grab(data, data_path)

        metric_tags = dict()
        for data_tag in data_tags or list():
            tag_value = grab(data, data_tag)
            if tag_value is not None:
                metric_tags[data_tag] = tag_value

        if metric_value is None:
            # this would be ok, but eventually confuse people as it will show up on every request
            log.debug(f"Unable to extract '{data_path}' form '{data}', got '{type(metric_value)}'")
            return

        if data_type in [int, bool, str]:
            try:
                metric_value = data_type(grab(data, data_path))
            except Exception as e:
                log.error(f"Unable to convert FritzBox Lua value '{metric_value}' to '{data_type}': {e}")

            metric = FritzMeasurement(metric_name, metric_value, self.config.box_tag, additional_tags=metric_tags)

            self.current_result_list.append(metric)
            return

        if type(metric_value) != data_type:
            log.error(f"FritzBox metric type '{data_type}' does not match data: {type(metric_value)}")
            return

        if data_type == list and data_next is not None:
            [self.extract_value(next_metric_value, metric_name, data_next) for next_metric_value in metric_value]
            return

        log.error(f"Unknown metric '{data_path}' form '{data}', with type '{type(metric_value)}' "
                  f"and defined type '{data_type}'")

    def query_service_data(self, service, discover=False):

        if not isinstance(service, FritzBoxLuaService):
            log.error("Query service must be of type 'FritzBoxLuaService'")
            return

        if discover is False and (service.available is False or service.should_service_be_requested() is False):
            return

        # request data
        result = self.request(service.page)

        if result is None:
            log.error(f"Unable to request FritzBox service '{service.name}'")
            if discover is True:
                log.info(f"FritzBox service '{service.name}'. Service will be disabled.")
                service.available = False
            return

        log.debug(f"Request FritzBox service '{service.name}' returned successfully")

        # set time stamp of this query
        service.set_last_query_now()

        # Request every param
        for metric_name, metric_params in service.value_instances.items():
            self.extract_value(result, metric_name, metric_params)

        return
