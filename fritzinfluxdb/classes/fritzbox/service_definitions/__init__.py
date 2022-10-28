# -*- coding: utf-8 -*-
#  Copyright (c) 2022 - 2022 Ricardo Bartels. All rights reserved.
#
#  fritzinfluxdb.py
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see file LICENSE.txt included in this
#  repository or visit: <https://opensource.org/licenses/MIT>.

tr069_services = list()
lua_services = list()

import fritzinfluxdb.classes.fritzbox.service_definitions.connection_info
import fritzinfluxdb.classes.fritzbox.service_definitions.homeauto
import fritzinfluxdb.classes.fritzbox.service_definitions.logs
import fritzinfluxdb.classes.fritzbox.service_definitions.network_hosts
import fritzinfluxdb.classes.fritzbox.service_definitions.system_stats
import fritzinfluxdb.classes.fritzbox.service_definitions.telephone_list
import fritzinfluxdb.classes.fritzbox.service_definitions.tr069
import fritzinfluxdb.classes.fritzbox.service_definitions.vpn_data
