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

log = get_logger()


class FritzBoxAction:

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

    available = True
    name = None
    value_instances = None
    interval = 10
    last_query = None

    def __init__(self, service_data=None):

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
        self.last_query = datetime.now(pytz.utc)

    def should_service_be_requested(self):

        if self.last_query and (datetime.now(pytz.utc)-self.last_query).total_seconds() < self.interval:
            return False

        return True


class FritzBoxTR069Service(FritzBoxService):

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


class FritzBoxLuaService(FritzBoxService):

    page = None

    def __init__(self, service_data=None):

        super().__init__(service_data)

        self.page = service_data.get("page")

        if self.page is None:
            do_error_exit(f"FritzBoxLuaService '{self.name}' instance has no 'page' defined")
            return

        self.validate_value_instances()

        # used for services parsing log entries
        self.track_measurements = bool(service_data.get("track", False))
        self.tracked_measurements = set()

    def validate_value_instances(self):

        for metric_name, metric_params in self.value_instances.items():

            if metric_params.get("data_path") is None and metric_params.get("value_function") is None:
                do_error_exit(f"FritzBoxLuaService '{self.name}' metric '{metric_name}' "
                              f"has no 'data_path' and no 'value_function' defined")

            if metric_params.get("type") is None:
                do_error_exit(f"FritzBoxLuaService '{self.name}' metric {metric_name} has no 'type' defined")

    def skip_tracked_measurement(self, measurement):

        if self.track_measurements is True and hash(measurement) in self.tracked_measurements:
            return True

        return False

    def add_tracked_measurement(self, measurement):

        if self.track_measurements is True:
            self.tracked_measurements.add(hash(measurement))
