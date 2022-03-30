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
# from fritzconnection.lib.fritzhosts import FritzHosts

from fritzinfluxdb.classes.fritzbox.config import FritzBoxConfig
from fritzinfluxdb.log import get_logger
from fritzinfluxdb.classes.fritzbox.service_handler import FritzBoxService
from fritzinfluxdb.classes.fritzbox.services import fritzbox_services
from fritzinfluxdb.classes.common import FritzMeasurement

log = get_logger()


class FritzBoxHandler:

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

        # parse services from fritzbox/services.py
        for fritzbox_service in fritzbox_services:
            new_service = FritzBoxService(fritzbox_service)

            # adjust request interval if necessary
            if self.config.request_interval > new_service.interval:
                new_service.interval = self.config.request_interval

            self.services.append(new_service)

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

    def discover_available_services(self):

        for service in self.services:
            self.query_service_data(service, True)

    def query_service_data(self, service, discover=False) -> list:

        return_data = list()

        if not isinstance(service, FritzBoxService):
            log.error("Query service must be of type 'FritzBoxService'")

        if discover is False and service.available is False:
            log.debug(f"Skipping disabled service: {service.name}")
            return return_data

        # Request every action
        for action in service.actions:

            if discover is False and action.available is False:
                log.debug(f"Skipping disabled action: {action.name}")
                continue

            # add parameters
            log.debug(f"Requesting {service.name} : {action.name} ({action.params})")
            call_result = None
            try:
                call_result = self.session.call_action(service.name, action.name, **action.params)
            except FritzServiceError:
                log.error(f"Requested invalid service: {service.name}")
                if discover is True:
                    service.available = False
            except FritzActionError:
                log.error(f"Requested invalid action '{action.name}' for service: {service.name}")
                if discover is True:
                    action.available = False
            except FritzConnectionException as e:
                if "401" in str(e):
                    log.error(f"Failed to connect to FritzBox '{self.config.hostname}' using credentials. "
                              "Check username and password!")
                else:
                    log.error(f"Failed to connect to FritzBox '{self.config.hostname}': {e}")
            except Exception as e:
                log.error(f"Unable to request FritzBox data: {e}")

            if call_result is not None:
                log.debug("Request returned successfully")

                # set time stamp of this query
                if discover is False:
                    service.set_last_query_now()

                for key, value in call_result.items():
                    log.debug(f"Response: {key} = {value}")

                    metric_name = service.value_instances.get(key, None)

                    if metric_name is not None:
                        return_data.append(
                            FritzMeasurement(metric_name, value, self.config.box_tag)
                        )

        return return_data

    async def query_loop(self, queue):
        while True:

            for service in self.services:
                if service.available is True and service.should_service_be_requested() is True:
                    for response in self.query_service_data(service) or list():
                        await queue.put(response)

            await asyncio.sleep(1)


class FritzboxLuaHandler:

    config = None
    session = None
    init_successful = False

    def __init__(self, config):
        if isinstance(config, FritzBoxConfig):
            self.config = config
        else:
            self.config = FritzBoxConfig(config)

        self.init_successful = False
        self.url = None
        self.sid = None

        proto = "http"
        if self.config.tls_enabled is True:
            proto = "https"

        # disable TLS insecure warnings if user explicitly switched off validation
        if bool(self.config.verify_tls) is False:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        self.url = f"{proto}://{self.config.hostname}"

        self.session = requests.Session()
        self.session.verify = self.config.verify_tls

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

    async def query_loop(self, queue):
        while True:

#            for service in self.services:
#                if service.available is True and service.should_service_be_requested() is True:
#                    for response in self.query_service_data(service) or list():
#                        await queue.put(response)

            await asyncio.sleep(1)
