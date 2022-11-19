#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""Self care commands"""

from __future__ import annotations
from typing import List

import datetime
import math
import random
import time

import requests

import bot.commands


MOONBASE_TIME = datetime.timezone(-datetime.timedelta(hours=8), "Canada/Pacific")

MARCH_START = datetime.datetime(2020, 3, 1, 0, tzinfo=MOONBASE_TIME)

BUS_START = datetime.datetime(2022, 11, 12, 14, tzinfo=MOONBASE_TIME)
SHIFT_START = datetime.datetime(2022, 11, 12, 12, tzinfo=MOONBASE_TIME)
OMEGA_START = datetime.datetime(2022, 11, 19, 6, tzinfo=MOONBASE_TIME)
BUS_END = datetime.datetime(2022, 11, 19, 17, tzinfo=MOONBASE_TIME)

WEEKDAYS: List[str] = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]
SUFFIX: List[str] = ["th", "st", "nd", "rd"]
SHIFTS: List[str] = ["Alpha Flight", "Night Watch", "Zeta", "Dawn Guard"]
EXPANSIONS: List[str] = [
    "",  # 0 offset, and there is no day 0
    "Departure",
    "New Bussing Back",
    "The Open Road",
    "(Barely) Living Legends",
    "A Bus Forward",
    "(Guest) Callings",
    "The Heart of a Chat",
    "End of Days (Permatwilight)",
]


class BusIsComing(bot.commands.SimpleCommand):
    """Count down to Desert Bus (in Desert Bus Points"""

    def __init__(self) -> None:
        super().__init__("bus")

    def message(self) -> str:
        now: datetime.datetime = datetime.datetime.now(MOONBASE_TIME)

        if now < BUS_START:
            points: float = (BUS_START - now).total_seconds() / (8 * 3600 + 2 * 60)
            s_points: str = f"{points:.1f}" if points > 1 else f"{points:.2f}"

            return (
                "Bus Is Coming. "
                f"Auto-James must acquire {s_points} more points to summon The Bus."
            )

        if now > BUS_END:
            return (
                "Typical! You wait all year for a bus, "
                "and five shifts come along at once. "
                "Whelp, have to wait until next year now."
            )

        diff: datetime.timedelta = now - SHIFT_START
        shift: int
        times: int

        if now > OMEGA_START:
            omega_diff: datetime.timedelta = now - OMEGA_START
            shift = 1
            times = omega_diff.seconds
        else:
            shift = diff.seconds // (6 * 3600)
            times = diff.seconds - shift * 6 * 3600

        date: int = diff.days + 1

        shift_name = SHIFTS[shift % 4]
        time_str = f"{times // 3600}:{(times//60%60):02}:{(times%60):02}"

        total_shift = 4 * date + shift
        suffix: str = (
            SUFFIX[total_shift % 10]
            if total_shift % 10 < len(SUFFIX) and not (10 < total_shift < 13)
            else "th"
        )

        if now > OMEGA_START:
            expansion = "Hopecoming"
            shift_name = "Omega"
            date = "π"  # type: ignore
            shift = "e"  # type: ignore
        else:
            expansion = EXPANSIONS[date]

        return random.choice(
            [
                f"It is {time_str} on Desert Bus 2022, {date}.{shift} {expansion} ({shift_name})",
                f"It is {time_str} on {shift_name}, the {total_shift}{suffix} of Bus",
            ]
        )


class March(bot.commands.SimpleCommand):
    """Gets the current date in March 2020"""

    def __init__(self) -> None:
        super().__init__("truemarch")

    def message(self) -> str:
        now: datetime.datetime = datetime.datetime.now(MOONBASE_TIME)

        date: int = (now - MARCH_START).days + 1
        month: str = "March"
        dow: str = WEEKDAYS[now.weekday()]

        suffix: str = (
            SUFFIX[date % 10] if date % 10 < len(SUFFIX) and not (10 < date < 13) else "th"
        )

        return f"Today is {dow}, {date}{suffix} of {month} 2020"


class BusStop(bot.commands.SimpleCommand):
    def __init__(self) -> None:
        super().__init__("busstop")

    @staticmethod
    def hours(amount: float) -> float:
        return math.log(amount + 14.2857, 1.07) - math.log(15.2857, 1.07) + 1

    def message(self) -> str:
        amount = requests.get("https://desertbus.org/wapi/init").json()["total"]
        hours = BusStop.hours(amount)

        end = time.mktime(BUS_START.utctimetuple())
        end += round(3600 * hours)
        end = int(end)

        return f"The next bus stop on the time table is <t:{end}:R>!"
