# -*- coding: utf-8 -*-
#
#  fritzinfluxdb.py
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see file LICENSE.txt included in this
#  repository or visit: <https://opensource.org/licenses/MIT>.

import asyncio

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

#        import pprint

#        for service, inst in self.session.services.items():
#            print(service)
#            for action in inst.actions:
#                pprint.pprint(action)

#        pprint.pprint(FritzHosts(fc=self.session).get_hosts_info())
        log.info("Successfully connected to FritzBox")
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
