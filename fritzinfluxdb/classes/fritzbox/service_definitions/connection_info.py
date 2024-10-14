# -*- coding: utf-8 -*-
#  Copyright (c) 2022 - 2023 Ricardo Bartels. All rights reserved.
#
#  fritzinfluxdb.py
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see file LICENSE.txt included in this
#  repository or visit: <https://opensource.org/licenses/MIT>.

from fritzinfluxdb.common import grab
from fritzinfluxdb.classes.fritzbox.service_definitions import lua_services
from fritzinfluxdb.classes.fritzbox.model import FritzBoxLinkTypes


def prepare_json_response_data(response):
    """
    handler to prepare returned json data for parsing
    """

    return response.json()

def exclude_filter_docsis30(data):

    return "docsis30" not in grab(data, "data.channelDs", fallback={}).keys()


def exclude_filter_docsis31(data):
    return "docsis31" not in grab(data, "data.channelDs", fallback={}).keys()


lua_services.append({
        "name": "DSL Info",
        "os_min_versions": "7.29",
        "method": "POST",
        "params": {
            "page": "dslOv",
            "xhrId": "all",
            "xhr": 1,
            "useajax": 1
        },
        "link_type": FritzBoxLinkTypes.DSL,
        "response_parser": prepare_json_response_data,
        "interval": 600,
        "value_instances": {
            "dsl_line_length": {
                "data_path": "data.connectionData.lineLength",
                "type": int
            },
            "dsl_dslam_vendor": {
                "data_path": "data.connectionData.dslamId",
                "type": str
            },
            "dsl_dslam_sw_version": {
                "data_path": "data.connectionData.version",
                "type": str
            },
            "dsl_line_mode": {
                "data_path": "data.connectionData.line.0.mode",
                "type": str
            }
        }
    }
)

lua_services.append({
        "name": "Cable Info",
        "os_min_versions": "7.29",
        "method": "POST",
        "params": {
            "page": "docOv",
            "xhrId": "all",
            "xhr": 1
        },
        "link_type": FritzBoxLinkTypes.Cable,
        "response_parser": prepare_json_response_data,
        "interval": 600,
        "value_instances": {
            "cable_cmts_vendor": {
                "data_path": "data.connectionData.externApValue",
                "type": str
            },
            "cable_modem_version": {
                "data_path": "data.connectionData.version",
                "type": str
            },
            "cable_line_mode": {
                "data_path": "data.connectionData.line.0.mode",
                "type": str
            },
            "cable_num_ds_channels": {
                "type": int,
                "value_function": (lambda data:
                                   sum([len(x) for x in grab(data, "data.connectionData.dsFreqs.values",
                                                             fallback=dict()).values()])
                                   ),
            },
            "cable_num_us_channels": {
                "type": int,
                "value_function": (lambda data:
                                   sum([len(x) for x in grab(data, "data.connectionData.usFreqs.values",
                                                             fallback=dict()).values()])
                                   ),
            }
        }
    }
)

lua_services.append({
        "name": "Cable Channel Info",
        "os_min_versions": "7.29",
        "os_max_versions": "7.57",
        "method": "POST",
        "params": {
            "page": "docInfo",
            "xhrId": "all",
            "xhr": 1
        },
        "link_type": FritzBoxLinkTypes.Cable,
        "response_parser": prepare_json_response_data,
        "value_instances": {
            "cable_channel_ds_docsis31_type": {
                "data_path": "data.channelDs.docsis31",
                "type": list,
                "next": {
                    "type": str,
                    "value_function": lambda data: data.get("type"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis31
            },
            "cable_channel_ds_docsis31_power_level": {
                "data_path": "data.channelDs.docsis31",
                "type": list,
                "next": {
                    "type": str,
                    "value_function": lambda data: data.get("powerLevel"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis31
            },
            "cable_channel_ds_docsis31_channel": {
                "data_path": "data.channelDs.docsis31",
                "type": list,
                "next": {
                    "type": int,
                    "value_function": lambda data: data.get("channel"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis31
            },
            "cable_channel_ds_docsis31_frequency": {
                "data_path": "data.channelDs.docsis31",
                "type": list,
                "next": {
                    "type": str,
                    "value_function": lambda data: data.get("frequency"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis31
            },
            "cable_channel_ds_docsis30_type": {
                "data_path": "data.channelDs.docsis30",
                "type": list,
                "next": {
                    "type": str,
                    "value_function": lambda data: data.get("type"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis30
            },
            "cable_channel_ds_docsis30_power_level": {
                "data_path": "data.channelDs.docsis30",
                "type": list,
                "next": {
                    "type": str,
                    "value_function": lambda data: data.get("powerLevel"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis30
            },
            "cable_channel_ds_docsis30_channel": {
                "data_path": "data.channelDs.docsis30",
                "type": list,
                "next": {
                    "type": int,
                    "value_function": lambda data: data.get("channel"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis30
            },
            "cable_channel_ds_docsis30_frequency": {
                "data_path": "data.channelDs.docsis30",
                "type": list,
                "next": {
                    "type": str,
                    "value_function": lambda data: data.get("frequency"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis30
            },
            "cable_channel_ds_docsis30_latency": {
                "data_path": "data.channelDs.docsis30",
                "type": list,
                "next": {
                    "type": float,
                    "value_function": lambda data: data.get("latency"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis30
            },
            "cable_channel_ds_docsis30_mse": {
                "data_path": "data.channelDs.docsis30",
                "type": list,
                "next": {
                    "type": float,
                    "value_function": lambda data: data.get("mse"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis30
            },
            "cable_channel_ds_docsis30_corrected_errors": {
                "data_path": "data.channelDs.docsis30",
                "type": list,
                "next": {
                    "type": int,
                    "value_function": lambda data: data.get("corrErrors"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis30
            },
            "cable_channel_ds_docsis30_non_corrected_errors": {
                "data_path": "data.channelDs.docsis30",
                "type": list,
                "next": {
                    "type": int,
                    "value_function": lambda data: data.get("nonCorrErrors"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis30
            },
            "cable_channel_us_docsis31_type": {
                "data_path": "data.channelUs.docsis31",
                "type": list,
                "next": {
                    "type": str,
                    "value_function": lambda data: data.get("type"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis31
            },
            "cable_channel_us_docsis31_power_level": {
                "data_path": "data.channelUs.docsis31",
                "type": list,
                "next": {
                    "type": str,
                    "value_function": lambda data: data.get("powerLevel"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis31
            },
            "cable_channel_us_docsis31_channel": {
                "data_path": "data.channelUs.docsis31",
                "type": list,
                "next": {
                    "type": int,
                    "value_function": lambda data: data.get("channel"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis31
            },
            "cable_channel_us_docsis31_frequency": {
                "data_path": "data.channelUs.docsis31",
                "type": list,
                "next": {
                    "type": str,
                    "value_function": lambda data: data.get("frequency"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis31
            },
            "cable_channel_us_docsis31_multiplex": {
                "data_path": "data.channelUs.docsis31",
                "type": list,
                "next": {
                    "type": str,
                    "value_function": lambda data: data.get("multiplex"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis31
            },
            "cable_channel_us_docsis30_type": {
                "data_path": "data.channelUs.docsis30",
                "type": list,
                "next": {
                    "type": str,
                    "value_function": lambda data: data.get("type"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis30
            },
            "cable_channel_us_docsis30_power_level": {
                "data_path": "data.channelUs.docsis30",
                "type": list,
                "next": {
                    "type": str,
                    "value_function": lambda data: data.get("powerLevel"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis30
            },
            "cable_channel_us_docsis30_channel": {
                "data_path": "data.channelUs.docsis30",
                "type": list,
                "next": {
                    "type": int,
                    "value_function": lambda data: data.get("channel"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis30
            },
            "cable_channel_us_docsis30_frequency": {
                "data_path": "data.channelUs.docsis30",
                "type": list,
                "next": {
                    "type": str,
                    "value_function": lambda data: data.get("frequency"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis30
            },
            "cable_channel_us_docsis30_multiplex": {
                "data_path": "data.channelUs.docsis30",
                "type": list,
                "next": {
                    "type": str,
                    "value_function": lambda data: data.get("multiplex"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis30
            },
        }
    }
)

lua_services.append({
        "name": "Cable Channel Info",
        "os_min_versions": "7.58",
        "method": "POST",
        "params": {
            "page": "docInfo",
            "xhrId": "all",
            "xhr": 1
        },
        "link_type": FritzBoxLinkTypes.Cable,
        "response_parser": prepare_json_response_data,
        "value_instances": {

            # DOCSIS 3.1 down stream
            "cable_channel_ds_docsis31_power_level": {
                "data_path": "data.channelDs.docsis31",
                "type": list,
                "next": {
                    "type": str,
                    "value_function": lambda data: data.get("powerLevel"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis31
            },
            "cable_channel_ds_docsis31_non_corrected_errors": {
                "data_path": "data.channelDs.docsis31",
                "type": list,
                "next": {
                    "type": int,
                    "value_function": lambda data: data.get("nonCorrErrors"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis31
            },
            "cable_channel_ds_docsis31_modulation": {
                "data_path": "data.channelDs.docsis31",
                "type": list,
                "next": {
                    "type": str,
                    "value_function": lambda data: data.get("modulation"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis31
            },
            "cable_channel_ds_docsis31_plc": {
                "data_path": "data.channelDs.docsis31",
                "type": list,
                "next": {
                    "type": str,
                    "value_function": lambda data: data.get("plc"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis31
            },
            "cable_channel_ds_docsis31_mer": {
                "data_path": "data.channelDs.docsis31",
                "type": list,
                "next": {
                    "type": str,
                    "value_function": lambda data: data.get("mer"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis31
            },
            "cable_channel_ds_docsis31_fft": {
                "data_path": "data.channelDs.docsis31",
                "type": list,
                "next": {
                    "type": str,
                    "value_function": lambda data: data.get("fft"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis31
            },
            "cable_channel_ds_docsis31_frequency": {
                "data_path": "data.channelDs.docsis31",
                "type": list,
                "next": {
                    "type": str,
                    "value_function": lambda data: data.get("frequency"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis31
            },

            # DOCSIS 3.0 down stream
            "cable_channel_ds_docsis30_power_level": {
                "data_path": "data.channelDs.docsis30",
                "type": list,
                "next": {
                    "type": str,
                    "value_function": lambda data: data.get("powerLevel"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis30
            },
            "cable_channel_ds_docsis30_non_corrected_errors": {
                "data_path": "data.channelDs.docsis30",
                "type": list,
                "next": {
                    "type": int,
                    "value_function": lambda data: data.get("nonCorrErrors"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis30
            },
            "cable_channel_ds_docsis30_modulation": {
                "data_path": "data.channelDs.docsis30",
                "type": list,
                "next": {
                    "type": str,
                    "value_function": lambda data: data.get("modulation"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis30
            },
            "cable_channel_ds_docsis30_corrected_errors": {
                "data_path": "data.channelDs.docsis30",
                "type": list,
                "next": {
                    "type": int,
                    "value_function": lambda data: data.get("corrErrors"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis30
            },
            "cable_channel_ds_docsis30_latency": {
                "data_path": "data.channelDs.docsis30",
                "type": list,
                "next": {
                    "type": float,
                    "value_function": lambda data: data.get("latency"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis30
            },
            "cable_channel_ds_docsis30_mse": {
                "data_path": "data.channelDs.docsis30",
                "type": list,
                "next": {
                    "type": float,
                    "value_function": lambda data: data.get("mse"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis30
            },
            "cable_channel_ds_docsis30_frequency": {
                "data_path": "data.channelDs.docsis30",
                "type": list,
                "next": {
                    "type": str,
                    "value_function": lambda data: data.get("frequency"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis30
            },

            # DOCSIS 3.1 up stream
            "cable_channel_us_docsis31_power_level": {
                "data_path": "data.channelUs.docsis31",
                "type": list,
                "next": {
                    "type": str,
                    "value_function": lambda data: data.get("powerLevel"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis31
            },
            "cable_channel_us_docsis31_modulation": {
                "data_path": "data.channelUs.docsis31",
                "type": list,
                "next": {
                    "type": str,
                    "value_function": lambda data: data.get("modulation"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis31
            },
            "cable_channel_us_docsis31_activesub": {
                "data_path": "data.channelUs.docsis31",
                "type": list,
                "next": {
                    "type": int,
                    "value_function": lambda data: data.get("activesub"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis31
            },
            "cable_channel_us_docsis31_fft": {
                "data_path": "data.channelUs.docsis31",
                "type": list,
                "next": {
                    "type": str,
                    "value_function": lambda data: data.get("fft"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis31
            },
            "cable_channel_us_docsis31_frequency": {
                "data_path": "data.channelUs.docsis31",
                "type": list,
                "next": {
                    "type": str,
                    "value_function": lambda data: data.get("frequency"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis31
            },

            # DOCSIS 3.0 up stream
            "cable_channel_us_docsis30_power_level": {
                "data_path": "data.channelUs.docsis30",
                "type": list,
                "next": {
                    "type": str,
                    "value_function": lambda data: data.get("powerLevel"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis30
            },
            "cable_channel_us_docsis30_modulation": {
                "data_path": "data.channelUs.docsis30",
                "type": list,
                "next": {
                    "type": str,
                    "value_function": lambda data: data.get("modulation"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis30
            },
            "cable_channel_us_docsis30_multiplex": {
                "data_path": "data.channelUs.docsis30",
                "type": list,
                "next": {
                    "type": str,
                    "value_function": lambda data: data.get("multiplex"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis30
            },
            "cable_channel_us_docsis30_frequency": {
                "data_path": "data.channelUs.docsis30",
                "type": list,
                "next": {
                    "type": str,
                    "value_function": lambda data: data.get("frequency"),
                    "tags_function": lambda data: {"id": data.get("channelID")}
                },
                "exclude_filter_function": exclude_filter_docsis30
            },
        }
    }
)
