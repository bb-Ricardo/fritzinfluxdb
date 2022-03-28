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
    actions = None
    value_instances = None
    interval = 10
    last_query = None

    def __init__(self, service_data=None):

        if not isinstance(service_data, dict):
            do_error_exit("FritzBoxService service data must be a dict")
            return

        self.name = service_data.get("name", None)
        self.actions = list()
        self.value_instances = list()
        self.interval = self.interval

        if self.name is None:
            do_error_exit("FritzboxService instance has no name")
            return

        for action in service_data.get("actions", list()):
            self.add_action(action)

        self.add_value_instances(service_data.get("value_instances", dict()))

    def add_action(self, action: Union[AnyStr, Dict] = None) -> None:

        if action is None:
            log.error(f"Missing action for FritzBoxService '{self.name}'")
            return

        action_instance = FritzBoxAction(action)

        if action_instance.name is None:
            log.error(f"Failed to add action to FritzBoxService '{self.name}': {action}")
        else:
            self.actions.append(action_instance)

    def add_value_instances(self, data: Dict = None) -> None:

        if data is None:
            log.error(f"Missing value instances data for FritzBoxService '{self.name}'")
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
