# -*- coding: utf-8 -*-
#  Copyright (c) 2022 - 2023 Ricardo Bartels. All rights reserved.
#
#  fritzinfluxdb.py
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see file LICENSE.txt included in this
#  repository or visit: <https://opensource.org/licenses/MIT>.

from fritzinfluxdb.classes.fritzbox.service_definitions import tr069_services
from fritzinfluxdb.classes.fritzbox.model import FritzBoxLinkTypes

tr069_services.extend([
    {
        "name": "WANCommonIFC",
        "actions": [
            "GetAddonInfos",
            "GetCommonLinkProperties"
        ],
        "value_instances": {
            "NewByteSendRate": "sendrate:int",
            "NewByteReceiveRate": "receiverate:int",
            "NewX_AVM_DE_TotalBytesSent64": "totalbytessent:int",
            "NewX_AVM_DE_TotalBytesReceived64": "totalbytesreceived:int",
            "NewLayer1DownstreamMaxBitRate": "downstreammax:int",
            "NewLayer1UpstreamMaxBitRate": "upstreammax:int",
            "NewPhysicalLinkStatus": "physicallinkstatus:str",
            "NewX_AVM_DE_WANAccessType": "physicallinktype:str"
        }
    },
    {
        "name": "WANIPConn",
        "actions": [
            "GetStatusInfo",
            "X_AVM_DE_GetExternalIPv6Address",
            "X_AVM_DE_GetIPv6Prefix"
        ],
        "value_instances": {
            "NewUptime": "linkuptime:int",
            "NewConnectionStatus": "connection_status:str",
            "NewLastConnectionError": "last_connection_error:str",
            "NewExternalIPv6Address": "external_ipv6:str",
            "NewIPv6Prefix": "ipv6_prefix:str",
            "NewPrefixLength": "ipv6_prefix_length:int"
        }
    },
    {
        "name": "WANCommonInterfaceConfig:1",
        "actions": ["GetCommonLinkProperties"],
        "value_instances": {
            "NewLayer1DownstreamMaxBitRate": "downstreamphysicalmax:int",
            "NewLayer1UpstreamMaxBitRate": "upstreamphysicalmax:int"
        }
    },
    {
        "name": "WANCommonInterfaceConfig",
        "actions": [
            {
                "name": "X_AVM-DE_GetOnlineMonitor",
                "params": {
                    "NewSyncGroupIndex": 0
                }
            }
        ],
        "value_instances": {
            "NewLayer1DownstreamMaxBitRate": "downstreamphysicalmax:int",
            "NewLayer1UpstreamMaxBitRate": "upstreamphysicalmax:int"
        }
    },
    {
        "name": "DeviceInfo",
        "actions": ["GetInfo"],
        "value_instances": {
            "NewUpTime": "systemuptime:int",
            "NewDescription": "description:str",
            "NewSerialNumber": "serialnumber:str",
            "NewModelName": "model:str",
            "NewSoftwareVersion": "softwareversion:str",
        },
    },
    {
        "name": "LANEthernetInterfaceConfig:1",
        "actions": ["GetStatistics"],
        "value_instances": {
            "NewBytesReceived": "lan_totalbytesreceived:int",
            "NewBytesSent": "lan_totalbytessent:int"
        }
    },
    {
        "name": "WANDSLInterfaceConfig",
        "actions": [
            "GetInfo",
            "GetStatisticsTotal",
            "X_AVM-DE_GetDSLInfo"
        ],
        "link_type": FritzBoxLinkTypes.DSL,
        "value_instances": {
            "NewDownstreamMaxRate": "maxBitRate_downstream:int",
            "NewUpstreamMaxRate": "maxBitRate_upstream:int",
            "NewDownstreamCurrRate": "downstream_dsl_sync_max:int",
            "NewUpstreamCurrRate": "upstream_dsl_sync_max:int",
            "NewDownstreamNoiseMargin": "snr_downstream:int",
            "NewUpstreamNoiseMargin": "snr_upstream:int",
            "NewDownstreamAttenuation": "attenuation_downstream:int",
            "NewUpstreamAttenuation": "attenuation_upstream:int",
            "NewSeverelyErroredSecs": "severely_errored_seconds:int",
            "NewErroredSecs": "errored_seconds:int",
            "NewCRCErrors": "crc_errors:int",
            "NewDownstreamPower": "power_downstream:int",
            "NewUpstreamPower": "power_upstream:int"
        }
    },
    {
        "name": "UserInterface:1",
        "actions": ["GetInfo"],
        "value_instances": {
            "NewUpgradeAvailable": "upgrade_available:bool",
            "NewX_AVM-DE_UpdateState": "update_state:str"
        }
    },
    {
        "name": "WANPPPConnection:1",
        "actions": ["GetInfo"],
        "link_type": FritzBoxLinkTypes.DSL,
        "value_instances": {
            "NewExternalIPAddress": "external_ip:str",
            "NewLastAuthErrorInfo": "last_auth_error:str",
            "NewPPPoEACName": "remote_pop:str",
            "NewUptime": "phyiscal_linkuptime:int",
            "NewConnectionStatus": "physical_connection_status:str",
            "NewLastConnectionError": "last_connection_error:str"
        }
    },
    {
        "name": "WANIPConnection:1",
        "actions": ["GetInfo"],
        "link_type": FritzBoxLinkTypes.Cable,
        "value_instances": {
            "NewExternalIPAddress": "external_ip:str",
            "NewUptime": "phyiscal_linkuptime:int",
            "NewConnectionStatus": "physical_connection_status:str",
            "NewLastConnectionError": "last_connection_error:str"
        }
    },
    {
        "name": "LANHostConfigManagement",
        "actions": ["GetInfo"],
        "value_instances": {
            "NewDNSServers": "internal_dns_servers:str"
        }
    },
    {
        "name": "WLANConfiguration:1",
        "actions": [
            "GetInfo",
            "GetTotalAssociations"
        ],
        "value_instances": {
            "NewStatus": "wlan1_status:str",
            "NewChannel": "wlan1_channel:int",
            "NewSSID": "wlan1_ssid:str",
            "NewStandard": "wlan1_802.11_standard:str",
            "NewTotalAssociations": "wlan1_associations:int"
        }
    },
    {
        "name": "WLANConfiguration:2",
        "actions": [
            "GetInfo",
            "GetTotalAssociations"
        ],
        "value_instances": {
            "NewStatus": "wlan2_status:str",
            "NewChannel": "wlan2_channel:int",
            "NewSSID": "wlan2_ssid:str",
            "NewStandard": "wlan2_802.11_standard:str",
            "NewTotalAssociations": "wlan2_associations:int"
        }
    },
    {
        "name": "WLANConfiguration:3",
        "actions": [
            "GetInfo",
            "GetTotalAssociations"
        ],
        "value_instances": {
            "NewStatus": "wlan3_status:str",
            "NewChannel": "wlan3_channel:int",
            "NewSSID": "wlan3_ssid:str",
            "NewStandard": "wlan3_802.11_standard:str",
            "NewTotalAssociations": "wlan3_associations:int"
        }
    },
    {
        "name": "X_AVM-DE_RemoteAccess",
        "actions": ["GetDDNSInfo"],
        "value_instances": {
            "NewEnabled": "ddns_enabled:bool",
            "NewProviderName": "ddns_provider_name:str",
            "NewDomain": "ddns_domain:str",
            "NewStatusIPv4": "ddns_status_ipv4:str",
            "NewStatusIPv6": "ddns_status_ipv6:str",
            "NewMode": "ddns_mode:str"
        }
    }
])
