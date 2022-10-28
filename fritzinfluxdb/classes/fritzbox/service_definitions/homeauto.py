# -*- coding: utf-8 -*-
#  Copyright (c) 2022 - 2022 Ricardo Bartels. All rights reserved.
#
#  fritzinfluxdb.py
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see file LICENSE.txt included in this
#  repository or visit: <https://opensource.org/licenses/MIT>.

import xmltodict

from fritzinfluxdb.common import grab
from fritzinfluxdb.classes.fritzbox.service_handler import FritzBoxLuaURLPath
from fritzinfluxdb.classes.fritzbox.service_definitions import lua_services


def avm_temp_map(value, input_min, input_max, output_min, output_max):
    """
    Map home temperature data for AVM devices back to °C
    """

    int_value = int(value)

    if int_value in [253, 254]:
        return float(int_value)
    if int_value < input_min:
        return float(input_min)
    if int_value > input_max:
        return float(input_max)

    return float((int_value-input_min)/(input_max-input_min)*(output_max-output_min)+output_min)


def prepare_response_data(response):
    """
    handler to prepare returned data for parsing
    """

    return xmltodict.parse(response.content)


lua_services.append(
    {
        "name": "Home Automation",
        "os_versions": [
            "7.29",
            "7.30",
            "7.31",
            "7.39",
            "7.50"
        ],
        "url_path": FritzBoxLuaURLPath.homeautomation,
        "method": "GET",
        "params": {
            "switchcmd": "getdevicelistinfos"
        },
        "response_parser": prepare_response_data,
        "value_instances": {
            # Base Data
            "ha_fw_version": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": str,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "data_path": "@fwversion"
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },
            "ha_product_name": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": str,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "data_path": "@productname"
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },
            "ha_manufacturer": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": str,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "data_path": "@manufacturer"
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },
            "ha_device_present": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": int,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "data_path": "present"
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },

            # Battery data
            "ha_battery_percent": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": int,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "data_path": "battery",
                    "exclude_filter_function": lambda data: "battery" not in data.keys()
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },
            "ha_battery_low": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": int,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "data_path": "batterylow",
                    "exclude_filter_function": lambda data: "batterylow" not in data.keys()
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },

            # Temperature
            "ha_temperature": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": float,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": lambda data: (
                        float((int(grab(data, "temperature.celsius")) + int(grab(data, "temperature.offset")))/10)
                    ),
                    "exclude_filter_function": lambda data: (
                        grab(data, "temperature.celsius") is None or grab(data, "temperature.offset") is None
                    )
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },

            "ha_temperature_celsius": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": float,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": lambda data: (
                        float(int(grab(data, "temperature.celsius")) / 10)
                    ),
                    "exclude_filter_function": lambda data: grab(data, "temperature.celsius") is None
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },

            "ha_temperature_offset": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": float,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": lambda data: (
                        float(int(grab(data, "temperature.offset")) / 10)
                    ),
                    "exclude_filter_function": lambda data: grab(data, "temperature.offset") is None
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },

            # Power
            "ha_powermeter_power": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": float,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": lambda data: (
                        float(int(grab(data, "powermeter.power")) / 1000)
                    ),
                    "exclude_filter_function": lambda data: grab(data, "powermeter.power") is None
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },
            "ha_powermeter_energy": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": float,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": lambda data: grab(data, "powermeter.energy"),
                    "exclude_filter_function": lambda data: grab(data, "powermeter.energy") is None
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },
            "ha_powermeter_voltage": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": float,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": lambda data: (
                        float(int(grab(data, "powermeter.voltage")) / 1000)
                    ),
                    "exclude_filter_function": lambda data: grab(data, "powermeter.voltage") is None
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },

            # Switch data
            "ha_switch_state": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": int,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": lambda data: "0"+grab(data, "switch.state", fallback="0"),
                    "exclude_filter_function": lambda data: "switch" not in data.keys()
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },
            "ha_switch_mode": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": str,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": lambda data: grab(data, "switch.mode", fallback=""),
                    "exclude_filter_function": lambda data: "switch" not in data.keys()
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },
            "ha_switch_lock": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": int,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": lambda data: "0" + grab(data, "switch.lock", fallback="0"),
                    "exclude_filter_function": lambda data: "switch" not in data.keys()
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },
            "ha_switch_devicelock": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": int,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": lambda data: "0" + grab(data, "switch.devicelock", fallback="0"),
                    "exclude_filter_function": lambda data: "switch" not in data.keys()
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },
            "ha_simpleonoff_state": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": int,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": lambda data: "0" + grab(data, "simpleonoff.state", fallback="0"),
                    "exclude_filter_function": lambda data: "simpleonoff" not in data.keys()
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },
            "ha_levelcontrol_level": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": int,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": lambda data: "0" + grab(data, "levelcontrol.levelpercentage", fallback="0"),
                    "exclude_filter_function": lambda data: "levelcontrol" not in data.keys()
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },
            "ha_heating_tist": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": float,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": lambda data: (
                        avm_temp_map("0" + grab(data, "hkr.tist", fallback="0"), 0, 120, 0, 60)
                    ),
                    "exclude_filter_function": lambda data: "hkr" not in data.keys()
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },
            "ha_heating_tsoll": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": float,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": lambda data: (
                        avm_temp_map("0" + grab(data, "hkr.tsoll", fallback="0"), 16, 56, 8, 28)
                    ),
                    "exclude_filter_function": lambda data: "hkr" not in data.keys()
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },
            "ha_heating_komfort": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": float,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": lambda data: (
                        avm_temp_map("0" + grab(data, "hkr.komfort", fallback="0"), 16, 56, 8, 28)
                    ),
                    "exclude_filter_function": lambda data: "hkr" not in data.keys()
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },
            "ha_heating_absenk": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": float,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": lambda data: (
                        avm_temp_map("0" + grab(data, "hkr.absenk", fallback="0"), 16, 56, 8, 28)
                    ),
                    "exclude_filter_function": lambda data: "hkr" not in data.keys()
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },
            "ha_heating_lock": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": int,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": lambda data: "0" + grab(data, "hkr.lock", fallback="0"),
                    "exclude_filter_function": lambda data: "hkr" not in data.keys()
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },
            "ha_heating_devicelock": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": int,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": lambda data: "0" + grab(data, "hkr.devicelock", fallback="0"),
                    "exclude_filter_function": lambda data: "hkr" not in data.keys()
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },
            "ha_heating_errorcode": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": int,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": lambda data: "0" + grab(data, "hkr.errorcode", fallback="0"),
                    "exclude_filter_function": lambda data: "hkr" not in data.keys()
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },
            "ha_heating_windowopenactiv": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": int,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": lambda data: "0" + grab(data, "hkr.windowopenactiv", fallback="0"),
                    "exclude_filter_function": lambda data: "hkr" not in data.keys()
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },
            "ha_heating_windowopenactiveendtime": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": int,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": lambda data: "0" + grab(data, "hkr.windowopenactiveendtime", fallback="0"),
                    "exclude_filter_function": lambda data: "hkr" not in data.keys()
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },
            "ha_heating_boostactive": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": int,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": lambda data: "0" + grab(data, "hkr.boostactive", fallback="0"),
                    "exclude_filter_function": lambda data: "hkr" not in data.keys()
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },
            "ha_heating_boostactiveendtime": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": int,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": lambda data: "0" + grab(data, "hkr.boostactiveendtime", fallback="0"),
                    "exclude_filter_function": lambda data: "hkr" not in data.keys()
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },
            "ha_heating_batterylow": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": int,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": lambda data: "0" + grab(data, "hkr.batterylow", fallback="0"),
                    "exclude_filter_function": lambda data: "hkr" not in data.keys()
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },
            "ha_heating_battery": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": int,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": lambda data: "0" + grab(data, "hkr.battery", fallback="0"),
                    "exclude_filter_function": lambda data: "hkr" not in data.keys()
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },
            "ha_heating_nextchange_endperiod": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": int,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": lambda data: "0" + grab(data, "hkr.nextchange.endperiod", fallback="0"),
                    "exclude_filter_function": lambda data: "hkr" not in data.keys()
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },
            "ha_heating_nextchange_tchange": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": float,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": lambda data: (
                        avm_temp_map("0" + grab(data, "hkr.nextchange.tchange", fallback="0"), 16, 56, 8, 28)
                    ),
                    "exclude_filter_function": lambda data: "hkr" not in data.keys()
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },
            "ha_heating_summeractive": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": int,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": lambda data: "0" + grab(data, "hkr.summeractive", fallback="0"),
                    "exclude_filter_function": lambda data: "hkr" not in data.keys()
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },
            "ha_heating_holidayactive": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": int,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": lambda data: "0" + grab(data, "hkr.holidayactive", fallback="0"),
                    "exclude_filter_function": lambda data: "hkr" not in data.keys()
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },
        }
    })
