# -*- coding: utf-8 -*-
#
#  fritzinfluxdb.py
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see file LICENSE.txt included in this
#  repository or visit: <https://opensource.org/licenses/MIT>.

from typing import Union, AnyStr, Dict
import pytz
from datetime import datetime

from fritzinfluxdb.common import do_error_exit
from fritzinfluxdb.log import get_logger
from fritzinfluxdb.classes.common import FritzMeasurement

log = get_logger()


class FritzBoxAction:
    """
        defines a single FritzBox query action
    """

    available = True

    def __init__(self, action: Union[AnyStr, Dict] = None) -> None:

        if action is None:
            do_error_exit("Missing action for FritzBoxAction")

        self.params = dict()
        if isinstance(action, str):
            self.name = action
        elif isinstance(action, dict):
            self.name = action.get("name", None)
            self.params = action.get("params", dict())
        else:
            do_error_exit(f"A FritzBoxAction param action must be a string or dict, got '{type(action)}'")

        if self.name is None:
            do_error_exit("FritzBoxAction name was not defined in action parameter")


class FritzBoxService:
    """
        base class to provide a FritzBox service. It is used to manage a single service request interval,
        keeping track of last query and if this service was enabled/disabled during discovery.
    """

    available = True
    name = None
    value_instances = None
    interval = 10
    last_query = None

    def __init__(self, service_data: Dict = None):

        if not isinstance(service_data, dict):
            do_error_exit(f"{self.__class__.name} service data must be a dict")
            return

        self.name = service_data.get("name")
        self.params = service_data.get("params")
        self.value_instances = dict()
        self.interval = service_data.get("interval", self.interval)

        if self.name is None:
            do_error_exit(f"{self.__class__.name} instance has no name")
            return

        self.add_value_instances(service_data.get("value_instances", dict()))

    def add_value_instances(self, data: Dict = None) -> None:

        if data is None:
            log.error(f"Missing value instances data for {self.__class__.name} '{self.name}'")
            return

        if not isinstance(data, dict):
            log.error(f"Data for value_instances must be a dict")
            return

        self.value_instances = data

        return

    def set_last_query_now(self):
        """
            needs to be called after every successful service query
        """
        self.last_query = datetime.now(pytz.utc)

    def should_be_requested(self):
        """
        determines if conditions are fulfilled to request this service again
        """

        if self.available is False:
            return False

        if self.last_query and (datetime.now(pytz.utc)-self.last_query).total_seconds() < self.interval:
            return False

        return True


class FritzBoxTR069Service(FritzBoxService):
    """
    a single TR069 service
    """

    actions = None

    def __init__(self, service_data=None):

        super().__init__(service_data)

        self.actions = list()

        for action in service_data.get("actions", list()):
            self.add_action(action)

    def add_action(self, action: Union[AnyStr, Dict] = None) -> None:

        if action is None:
            log.error(f"Missing action for FritzBoxTR069Service '{self.name}'")
            return

        action_instance = FritzBoxAction(action)

        if action_instance.name is None:
            log.error(f"Failed to add action to FritzBoxTR069Service '{self.name}': {action}")
        else:
            self.actions.append(action_instance)


class FritzBoxLuaURLPath:
    data = "/data.lua"
    homeautomation = "/webservices/homeautoswitch.lua"
    foncalls_list = "/fon_num/foncalls_list.lua"


class FritzBoxLuaService(FritzBoxService):
    """
    a single Lua service
    """

    os_versions = None
    url_path = None
    default_method = "GET"
    default_url_path = FritzBoxLuaURLPath.data

    def __init__(self, service_data=None):

        super().__init__(service_data)

        self.url_path = service_data.get("url_path", self.default_url_path)
        self.os_versions = service_data.get("os_versions", list())
        self.method = service_data.get("method", self.default_method)
        self.response_parser = service_data.get("response_parser", self.response_parser)

        if len(self.url_path) == 0:
            do_error_exit(f"FritzBoxLuaService '{self.name}' instance has no url_path defined")

        if len(self.os_versions) == 0:
            do_error_exit(f"FritzBoxLuaService '{self.name}' instance has no supported 'os_versions' defined")

        if not callable(self.response_parser):
            do_error_exit(f"FritzBoxLuaService '{self.name}' instance 'response_parser' is not a callable function")

        if self.method not in ["GET", "POST", "HEAD"]:
            do_error_exit(f"FritzBoxLuaService '{self.name}' instance 'method' invalid: {self.method}")

        self.validate_value_instances()

        # used for services parsing log entries
        self.track_measurements = bool(service_data.get("track", False))
        self.tracked_measurements = set()

    def validate_value_instances(self):
        """
        validate if necessary information has been provided
        """

        for metric_name, metric_params in self.value_instances.items():

            if metric_params.get("data_path") is None and metric_params.get("value_function") is None:
                do_error_exit(f"FritzBoxLuaService '{self.name}' metric '{metric_name}' "
                              f"has no 'data_path' and no 'value_function' defined")

            if metric_params.get("type") is None:
                do_error_exit(f"FritzBoxLuaService '{self.name}' metric {metric_name} has no 'type' defined")

    def skip_tracked_measurement(self, measurement: FritzMeasurement):
        """
        check if measurement has already been generated. This is helpful reading logs and only add logs
        which have not been seen before
        """

        if self.track_measurements is True and hash(measurement) in self.tracked_measurements:
            return True

        return False

    def add_tracked_measurement(self, measurement: FritzMeasurement):
        """
        adds a measurement to the tracking list
        """

        if self.track_measurements is True:
            self.tracked_measurements.add(hash(measurement))

    @staticmethod
    def response_parser(response):
        """
        handler to prepare returned data for parsing
        """

        return response.text
