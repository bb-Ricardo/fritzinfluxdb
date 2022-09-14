# -*- coding: utf-8 -*-
#
#  fritzinfluxdb.py
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see file LICENSE.txt included in this
#  repository or visit: <https://opensource.org/licenses/MIT>.

from fritzinfluxdb.common import grab
from fritzinfluxdb.classes.fritzbox.service_handler import FritzBoxLuaURLPath

fritzbox_services = list()


def avm_temp_map(value, input_min, input_max, output_min, output_max):

    int_value = int(value)

    if int_value in [253, 254]:
        return float(int_value)
    if int_value < input_min:
        return float(input_min)
    if int_value > input_max:
        return float(input_max)

    return float((int_value-input_min)/(input_max-input_min)*(output_max-output_min)+output_min)


fritzbox_services.append(
    {
        "name": "Home Automation",
        "switchcmd": "getdevicelistinfos",
        "url_path": FritzBoxLuaURLPath.homeautomation,
        "os_versions": [
            "7.29",
            "7.30",
            "7.31",
            "7.39"
        ],
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
                }
            },
            "ha_product_name": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": str,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "data_path": "@productname"
                }
            },
            "ha_manufacturer": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": str,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "data_path": "@manufacturer"
                }
            },
            "ha_device_present": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": int,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "data_path": "present"
                }
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
                }
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
                }
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
                    "exclude_filter_function": lambda data: "temperature" not in data.keys()
                }
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
                    "exclude_filter_function": lambda data: "powermeter" not in data.keys()
                }
            },
            "ha_powermeter_energy": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": float,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": lambda data: grab(data, "powermeter.energy"),
                    "exclude_filter_function": lambda data: "powermeter" not in data.keys()
                }
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
                    "exclude_filter_function": lambda data: "powermeter" not in data.keys()
                }
            },

            # Switch data
            "ha_switch_sate": {
                "data_path": "devicelist.device",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": int,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": lambda data: "0"+grab(data, "switch.state", fallback="0"),
                    "exclude_filter_function": lambda data: "switch" not in data.keys()
                }
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
                }
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
                }
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
                }
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
                }
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
                }
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
                }
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
                }
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
                }
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
                }
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
                }
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
                }
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
                }
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
                }
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
                }
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
                }
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
                }
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
                }
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
                }
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
                }
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
                }
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
                }
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
                }
            },
        }
    })
