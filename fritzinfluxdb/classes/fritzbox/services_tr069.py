# -*- coding: utf-8 -*-
#
#  fritzinfluxdb.py
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see file LICENSE.txt included in this
#  repository or visit: <https://opensource.org/licenses/MIT>.

fritzbox_services = [
    {
        "name": "WANCommonIFC",
        "actions": [
            "GetAddonInfos",
            "GetCommonLinkProperties"
        ],
        "value_instances": {
            "NewByteSendRate": "sendrate",
            "NewByteReceiveRate": "receiverate",
            "NewX_AVM_DE_TotalBytesSent64": "totalbytessent",
            "NewX_AVM_DE_TotalBytesReceived64": "totalbytesreceived",
            "NewLayer1DownstreamMaxBitRate": "downstreammax",
            "NewLayer1UpstreamMaxBitRate": "upstreammax",
            "NewPhysicalLinkStatus": "physicallinkstatus",
            "NewWANAccessType": "physicallinktype"
        }
    },
    {
        "name": "WANIPConn",
        "actions": [
            "GetStatusInfo",
            "X_AVM_DE_GetExternalIPv6Address"
        ],
        "value_instances": {
            "NewUptime": "linkuptime",
            "NewConnectionStatus": "connection_status",
            "NewLastConnectionError": "last_connection_error",
            "NewExternalIPv6Address": "external_ipv6"
        }
    },
    {
        "name": "WANCommonInterfaceConfig:1",
        "actions": ["GetCommonLinkProperties"],
        "value_instances": {
            "NewLayer1DownstreamMaxBitRate": "downstreamphysicalmax",
            "NewLayer1UpstreamMaxBitRate": "upstreamphysicalmax"
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
            "NewLayer1DownstreamMaxBitRate": "downstreamphysicalmax",
            "NewLayer1UpstreamMaxBitRate": "upstreamphysicalmax"
        }
    },
    {
        "name": "DeviceInfo",
        "actions": ["GetInfo"],
        "value_instances": {
            "NewUpTime": "systemuptime",
            "NewDescription": "description",
            "NewSerialNumber": "serialnumber",
            "NewModelName": "model",
            "NewSoftwareVersion": "softwareversion",
        },
        "interval": 60
    },
    {
        "name": "LANEthernetInterfaceConfig:1",
        "actions": ["GetStatistics"],
        "value_instances": {
            "NewBytesReceived": "lan_totalbytesreceived",
            "NewBytesSent": "lan_totalbytessent"
        }
    },
    {
        "name": "WANDSLInterfaceConfig",
        "actions": [
            "GetInfo",
            "GetStatisticsTotal",
            "X_AVM-DE_GetDSLInfo"
        ],
        "value_instances": {
            "NewDownstreamMaxRate": "maxBitRate_downstream",
            "NewUpstreamMaxRate": "maxBitRate_upstream",
            "NewDownstreamCurrRate": "downstream_dsl_sync_max",
            "NewUpstreamCurrRate": "upstream_dsl_sync_max",
            "NewDownstreamNoiseMargin": "snr_downstream",
            "NewUpstreamNoiseMargin": "snr_upstream",
            "NewDownstreamAttenuation": "attenuation_downstream",
            "NewUpstreamAttenuation": "attenuation_upstream",
            "NewSeverelyErroredSecs": "severely_errored_seconds",
            "NewErroredSecs": "errored_seconds",
            "NewCRCErrors": "crc_errors",
            "NewDownstreamPower": "power_downstream",
            "NewUpstreamPower": "power_upstream"
        }
    },
    {
        "name": "UserInterface:1",
        "actions": ["GetInfo"],
        "value_instances": {
            "NewUpgradeAvailable": "upgrade_available",
            "NewX_AVM-DE_UpdateState": "update_state"
        }
    },
    {
        "name": "WANPPPConnection:1",
        "actions": ["GetInfo"],
        "value_instances": {
            "NewExternalIPAddress": "external_ip",
            "NewLastAuthErrorInfo": "last_auth_error",
            "NewPPPoEACName": "remote_pop",
            "NewUptime": "linkuptime",
            "NewConnectionStatus": "connection_status",
            "NewLastConnectionError": "last_connection_error"
        }
    },
    {
        "name": "WANIPConnection:1",
        "actions": ["GetInfo"],
        "value_instances": {
            "NewExternalIPAddress": "external_ip",
            "NewUptime": "linkuptime",
            "NewConnectionStatus": "connection_status",
            "NewLastConnectionError": "last_connection_error"
        }
    },
    {
        "name": "LANHostConfigManagement",
        "actions": ["GetInfo"],
        "value_instances": {
            "NewDNSServers": "internal_dns_servers"
        }
    },
    {
        # ToDo:
        #   * Dashboard
        "name": "WLANConfiguration:1",
        "actions": [
            "GetInfo",
            "GetTotalAssociations"
        ],
        "value_instances": {
            "NewStatus": "wlan1_status",
            "NewChannel": "wlan1_channel",
            "NewSSID": "wlan1_ssid",
            "NewStandard": "wlan1_802.11_standard",
            "NewTotalAssociations": "wlan1_associations"
        }
    },
    {
        # ToDo:
        #   * Dashboard
        "name": "WLANConfiguration:2",
        "actions": [
            "GetInfo",
            "GetTotalAssociations"
        ],
        "value_instances": {
            "NewStatus": "wlan2_status",
            "NewChannel": "wlan2_channel",
            "NewSSID": "wlan2_ssid",
            "NewStandard": "wlan2_802.11_standard",
            "NewTotalAssociations": "wlan2_associations"
        }
    },
    {
        # ToDo:
        #   * Dashboard
        "name": "WLANConfiguration:3",
        "actions": [
            "GetInfo",
            "GetTotalAssociations"
        ],
        "value_instances": {
            "NewStatus": "wlan3_status",
            "NewChannel": "wlan3_channel",
            "NewSSID": "wlan3_ssid",
            "NewStandard": "wlan3_802.11_standard",
            "NewTotalAssociations": "wlan3_associations"
        }
    },
    {
        # ToDo:
        #   * Dashboard
        "name": "X_AVM-DE_RemoteAccess",
        "actions": ["GetDDNSInfo"],
        "value_instances": {
            "NewEnabled": "ddns_enabled",
            "NewProviderName": "ddns_provider_name",
            "NewDomain": "ddns_domain",
            "NewStatusIPv4": "ddns_status_ipv4",
            "NewStatusIPv6": "ddns_status_ipv6",
            "NewMode": "ddns_mode"
        }
    }
]
