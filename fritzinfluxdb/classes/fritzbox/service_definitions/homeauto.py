# -*- coding: utf-8 -*-
#  Copyright (c) 2022 - 2022 Ricardo Bartels. All rights reserved.
#
#  fritzinfluxdb.py
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see file LICENSE.txt included in this
#  repository or visit: <https://opensource.org/licenses/MIT>.

"""
    FritzBox home automation interface description (German):
    https://avm.de/fileadmin/user_upload/Global/Service/Schnittstellen/AHA-HTTP-Interface.pdf
"""

import xmltodict
import random
from datetime import datetime

from fritzinfluxdb.common import grab, in_test_mode
from fritzinfluxdb.classes.fritzbox.service_handler import FritzBoxLuaURLPath
from fritzinfluxdb.classes.fritzbox.service_definitions import lua_services

home_automation_device_classes = {
    0:  "HAN-FUN",
    1:  "UNDEFINED 1",
    2:  "Light",
    3:  "UNDEFINED 3",
    4:  "Alarm Sensor",
    5:  "AVM Button",
    6:  "Heating Regulator",
    7:  "Energy Measurement",
    8:  "Temperature Sensor",
    9:  "Switchable Power Sockets",
    10: "AVM DECT Repeater",
    11: "Microphone",
    12: "UNDEFINED 12",
    13: "HAN-FUN-Unit",
    14: "UNDEFINED 14",
    15: "Switchable Device",
    16: "Dimmable Device",
    17: "Light with Adjustable Color",
    18: "Blinds"
}

hun_fun_unit_types = {
    "273": "SIMPLE_BUTTON",
    "256": "SIMPLE_ON_OFF_SWITCHABLE",
    "257": "SIMPLE_ON_OFF_SWITCH",
    "262": "AC_OUTLET",
    "263": "AC_OUTLET_SIMPLE_POWER_METERING",
    "264": "SIMPLE_LIGHT",
    "265": "DIMMABLE_LIGHT",
    "266": "DIMMER_SWITCH",
    "277": "COLOR_BULB",
    "278": "DIMMABLE_COLOR_BULB",
    "281": "BLIND",
    "282": "LAMELLAR",
    "512": "SIMPLE_DETECTOR",
    "513": "DOOR_OPEN_CLOSE_DETECTOR",
    "514": "WINDOW_OPEN_CLOSE_DETECTOR",
    "515": "MOTION_DETECTOR",
    "518": "FLOOD_DETECTOR",
    "519": "GLAS_BREAK_DETECTOR",
    "520": "VIBRATION_DETECTOR",
    "640": "SIREN"
}

hun_fun_interface_types = {
    "277": "KEEP_ALIVE",
    "256": "ALERT",
    "512": "ON_OFF",
    "513": "LEVEL_CTRL",
    "514": "COLOR_CTRL",
    "516": "OPEN_CLOSE",
    "517": "OPEN_CLOSE_CONFIG",
    "772": "SIMPLE_BUTTON",
    "1024": "SUOTA-Update"
}

test_data = None
test_file_location = "test/homeauto_sample.xml"
test_start_ts = datetime.now().timestamp()


def avm_temp_map(value, input_min, input_max, output_min, output_max):
    """
    Map home temperature data for AVM devices back to °C
    """

    int_value = int(value)

    if int_value in [253, 254]:
        return float(int_value)
    if int_value < input_min:
        return float(output_min)
    if int_value > input_max:
        return float(output_max)

    return float((int_value-input_min)/(input_max-input_min)*(output_max-output_min)+output_min)


def get_ha_temperature(data):

    if in_test_mode():
        return random.randrange(220, 250) / 10

    return float((int(grab(data, "temperature.celsius")) + int(grab(data, "temperature.offset")))/10)


def get_ha_powermeter_power(data):

    if in_test_mode():
        return random.randrange(300_000, 500_000) / 1000

    return float(int(grab(data, "powermeter.power")) / 1000)


def get_ha_powermeter_energy(data):

    energy = grab(data, "powermeter.energy")
    if in_test_mode():
        return float(energy) + float(datetime.now().timestamp() - test_start_ts)

    return energy


def get_ha_powermeter_voltage(data):

    if in_test_mode():
        return random.randrange(225_000, 234_000) / 1000

    return float(int(grab(data, "powermeter.voltage")) / 1000)


def get_ha_switch_state(data):

    if in_test_mode():
        return int((datetime.now().timestamp() - test_start_ts) / 1000) % 2

    return "0"+grab(data, "switch.state", fallback="0")


def get_ha_alert_state(data):

    if in_test_mode():
        return int((datetime.now().timestamp() - test_start_ts) / 600) % 2

    return "0"+grab(data, "alert.state", fallback="0")


def decode_function_bitmask(bitmask: int):

    return_values = list()
    # noinspection PyBroadException
    try:
        binary_value = int(bitmask)
    except Exception:
        return return_values

    for bit_shift, value in home_automation_device_classes.items():

        if binary_value & 1 << bit_shift:
            return_values.append(value)

    return return_values


def reformat_homeauto_device_list(data):

    device_list = data.get("devicelist")

    devices_by_id = {x.get("@id"): x for x in device_list.get("device", [])}

    hun_fun_device_id = 0  # these need to be skipped and only scraped for the @fwversion
    hun_fun_unit_id = 13   # these ones are kept

    new_device_list = list()
    for device in device_list.get("device", []):

        device_functions = decode_function_bitmask(device.get("@functionbitmask"))

        # add function list
        device["@devicefunctions"] = device_functions

        if home_automation_device_classes[hun_fun_device_id] in device_functions:
            continue

        if home_automation_device_classes[hun_fun_unit_id] in device_functions:

            parent_unit_id = grab(device, "etsiunitinfo.etsideviceid")
            if parent_unit_id is None:
                continue

            device["etsiunitinfo"]["unittype"] = hun_fun_unit_types.get(grab(device, "etsiunitinfo.unittype"), "")
            device["etsiunitinfo"]["interfaces"] = hun_fun_unit_types.get(grab(device, "etsiunitinfo.interfaces"), "")

            hun_fun_device_fw = devices_by_id.get(parent_unit_id, dict()).get("@fwversion")
            if hun_fun_device_fw is not None:
                device["@fwversion"] = hun_fun_device_fw

        new_device_list.append(device)

    data["devicelist"]["device"] = new_device_list
    return data


def prepare_response_data(response):
    """
    handler to prepare returned data for parsing

    Parameters
    ----------
    response: requests.response
        the FritzBox request response

    Return
    ------
    dict: xml response parsed to dict
    """

    global test_data

    if in_test_mode():
        if test_data is None:
            with open(test_file_location) as f:
                test_data = f.read()

        content = test_data
    else:
        content = response.content

    return reformat_homeauto_device_list(xmltodict.parse(content, force_list=('device',)))


lua_services.append(
    {
        "name": "Home Automation",
        "os_min_versions": "7.29",
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
            "ha_devicefunctions": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": str,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": lambda data: ", ".join(data.get("@devicefunctions"))
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
                    "value_function": get_ha_temperature,
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
                    "value_function": get_ha_powermeter_power,
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
                    "value_function": get_ha_powermeter_energy,
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
                    "value_function": get_ha_powermeter_voltage,
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
                    "value_function": get_ha_switch_state,
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

            # HUN-FUN device data
            "ha_hun_fun_interfaces": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": str,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": lambda data: grab(data, "etsiunitinfo.interfaces"),
                    "exclude_filter_function": lambda data: "etsiunitinfo" not in data.keys()
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },
            "ha_hun_fun_unittype": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": str,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": lambda data: grab(data, "etsiunitinfo.unittype"),
                    "exclude_filter_function": lambda data: "etsiunitinfo" not in data.keys()
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },

            # Colorcontrol
            # colorcontrol: { supported_modes: '5', current_mode: '1', hue: '35', saturation: '214', temperature: '' },
            "ha_colorcontrol_current_mode": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    "type": int,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": lambda data: "0" + grab(data, "colorcontrol.current_mode", fallback="0"),
                    "exclude_filter_function": lambda data: "colorcontrol" not in data.keys()
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },
            "ha_colorcontrol_hue": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    "type": int,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": lambda data: "0" + grab(data, "colorcontrol.hue", fallback="0"),
                    "exclude_filter_function": lambda data: "colorcontrol" not in data.keys()
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },
            "ha_colorcontrol_saturation": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    "type": int,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": lambda data: "0" + grab(data, "colorcontrol.saturation", fallback="0"),
                    "exclude_filter_function": lambda data: "colorcontrol" not in data.keys()
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },
            "ha_colorcontrol_temperature": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    "type": int,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": lambda data: "0" + grab(data, "colorcontrol.temperature", fallback="0"),
                    "exclude_filter_function": lambda data: "colorcontrol" not in data.keys()
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },

            # Alarm
            "ha_alert": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    "type": int,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": get_ha_alert_state,
                    "exclude_filter_function": lambda data: "alert" not in data.keys()
                },
                "exclude_filter_function": lambda data: "device" not in data.get("devicelist").keys()
            },

            # Heating
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
                        avm_temp_map("0" + grab(data, "hkr.tsoll", fallback="253"), 16, 56, 8, 28)
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
                        avm_temp_map("0" + grab(data, "hkr.komfort", fallback="253"), 16, 56, 8, 28)
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
                        avm_temp_map("0" + grab(data, "hkr.absenk", fallback="253"), 16, 56, 8, 28)
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
