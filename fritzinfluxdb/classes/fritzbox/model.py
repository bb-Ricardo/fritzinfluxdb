# -*- coding: utf-8 -*-
#  Copyright (c) 2022 - 2023 Ricardo Bartels. All rights reserved.
#
#  fritzinfluxdb.py
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see file LICENSE.txt included in this
#  repository or visit: <https://opensource.org/licenses/MIT>.

from fritzinfluxdb.log import get_logger

log = get_logger()


class FritzBoxLinkTypes:
    Fiber = "Fiber"
    Cable = "Cable"
    DSL = "DSL"
    NO_MODEM = "NoModem"
    Mobile = "Mobile"
    Other = "Other"


class FritzBoxModel:

    # this table is used if the link type could not be determined properly
    _fritzbox_model_link_types = {
        "3490": FritzBoxLinkTypes.DSL,
        "4020": FritzBoxLinkTypes.NO_MODEM,
        "4040": FritzBoxLinkTypes.NO_MODEM,
        "4060": FritzBoxLinkTypes.NO_MODEM,
        "5490": FritzBoxLinkTypes.Fiber,
        "5491": FritzBoxLinkTypes.Fiber,
        "5530": FritzBoxLinkTypes.Fiber,
        # "5550": FritzBoxLinkTypes.Fiber, # mixed
        "5590": FritzBoxLinkTypes.Fiber,
        "6430": FritzBoxLinkTypes.Cable,
        "6490": FritzBoxLinkTypes.Cable,
        "6590": FritzBoxLinkTypes.Cable,
        "6591": FritzBoxLinkTypes.Cable,
        "6660": FritzBoxLinkTypes.Cable,
        "6690": FritzBoxLinkTypes.Cable,
        "6820": FritzBoxLinkTypes.Mobile,
        "6850": FritzBoxLinkTypes.Mobile,
        "6890": FritzBoxLinkTypes.Mobile,
        "7362": FritzBoxLinkTypes.DSL,
        "7412": FritzBoxLinkTypes.DSL,
        "7430": FritzBoxLinkTypes.DSL,
        "7490": FritzBoxLinkTypes.DSL,
        "7510": FritzBoxLinkTypes.DSL,
        "7520": FritzBoxLinkTypes.DSL,
        "7530": FritzBoxLinkTypes.DSL,
        "7560": FritzBoxLinkTypes.DSL,
        "7580": FritzBoxLinkTypes.DSL,
        "7582": FritzBoxLinkTypes.DSL,
        "7583": FritzBoxLinkTypes.DSL,
        "7590": FritzBoxLinkTypes.DSL,

        # older models
        "3272": FritzBoxLinkTypes.DSL,
        "3370": FritzBoxLinkTypes.DSL,
        "3390": FritzBoxLinkTypes.DSL,
        "6340": FritzBoxLinkTypes.Cable,
        "6360": FritzBoxLinkTypes.Cable,
        "6810": FritzBoxLinkTypes.Mobile,
        "6840": FritzBoxLinkTypes.Mobile,
        "6842": FritzBoxLinkTypes.Mobile,
        "7272": FritzBoxLinkTypes.DSL,
        "7312": FritzBoxLinkTypes.DSL,
        "7320": FritzBoxLinkTypes.DSL,
        "7330": FritzBoxLinkTypes.DSL,
        "7340": FritzBoxLinkTypes.DSL,
        "7360": FritzBoxLinkTypes.DSL,
        "7369": FritzBoxLinkTypes.DSL,
        "7390": FritzBoxLinkTypes.DSL,
        "7581": FritzBoxLinkTypes.DSL
    }

    @classmethod
    def get_link_type(cls, model_name, discovered_link_mode):

        if discovered_link_mode is not None and discovered_link_mode != FritzBoxLinkTypes.Other:
            if discovered_link_mode not in FritzBoxLinkTypes.__dict__.values():
                log.info(f"Unknown FritzBox link type '{discovered_link_mode}'. "
                         f"Please report this link type as issue to the github_project")
            return discovered_link_mode

        for fb_model, link_type in cls._fritzbox_model_link_types.items():
            if fb_model in model_name:
                return link_type

        return FritzBoxLinkTypes.Other
