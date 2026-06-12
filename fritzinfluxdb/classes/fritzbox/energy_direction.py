# -*- coding: utf-8 -*-
#  Copyright (c) 2022 - 2023 Ricardo Bartels. All rights reserved.
#
#  fritzinfluxdb.py
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see file LICENSE.txt included in this
#  repository or visit: <https://opensource.org/licenses/MIT>.

"""
    Energy direction detection for FRITZ!Smart Energy 250.

    The Smart Energy 250 reports two sub-devices via AHA-HTTP-Interface:
      - AIN suffix "-1": grid import (Bezug, A+)
      - AIN suffix "-2": grid export (Einspeisung, A-)

    Both channels report the same instantaneous power value — only the
    cumulative energy counters (Wh) differ by direction. Since the counters
    have 1 Wh resolution, short polling intervals (< 60s) at low power
    levels produce zero deltas. A sliding window (default 300s) accumulates
    enough energy to reliably detect direction.
"""

import time
from collections import deque

from fritzinfluxdb.log import get_logger

log = get_logger()


class EnergyDirectionTracker:
    """
    Tracks energy counter readings per device and derives the current
    energy flow direction from a sliding window comparison.
    """

    def __init__(self, window_seconds=300):
        self.window_seconds = window_seconds
        self._history = {}

    def update(self, ain, energy_wh):
        now = time.monotonic()
        if ain not in self._history:
            self._history[ain] = deque()
        self._history[ain].append((now, energy_wh))

        cutoff = now - self.window_seconds - 30
        while self._history[ain] and self._history[ain][0][0] < cutoff:
            self._history[ain].popleft()

    def get_delta(self, ain):
        entries = self._history.get(ain)
        if not entries or len(entries) < 2:
            return None

        now = time.monotonic()
        target_time = now - self.window_seconds
        oldest = None
        for ts, val in entries:
            if ts <= target_time:
                oldest = (ts, val)
            else:
                break

        if oldest is None:
            oldest = entries[0]

        newest = entries[-1]
        if oldest[0] == newest[0]:
            return None

        return max(0, newest[1] - oldest[1])


_tracker = EnergyDirectionTracker()


def track_energy_reading(ain, energy_wh):
    _tracker.update(ain, energy_wh)


def get_energy_direction(bezug_ain, einsp_ain):
    b_delta = _tracker.get_delta(bezug_ain)
    e_delta = _tracker.get_delta(einsp_ain)

    if b_delta is None or e_delta is None:
        return "unknown"

    if e_delta > b_delta:
        return "export"
    elif b_delta > e_delta:
        return "import"
    else:
        return "balanced"


def get_energy_direction_numeric(bezug_ain, einsp_ain):
    direction = get_energy_direction(bezug_ain, einsp_ain)
    return {"export": -1, "import": 1, "balanced": 0, "unknown": 0}.get(direction, 0)


def get_net_power(power_w, bezug_ain, einsp_ain):
    direction = get_energy_direction(bezug_ain, einsp_ain)
    if direction == "export":
        return -abs(power_w)
    return abs(power_w)
