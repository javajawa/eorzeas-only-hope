#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""Self care commands"""

from __future__ import annotations
from typing import List

import datetime
import math
import time

import aiohttp

import bot.commands


MOONBASE_TIME = datetime.timezone(-datetime.timedelta(hours=8), "Canada/Pacific")

MARCH_START = datetime.datetime(2020, 3, 1, 0, tzinfo=MOONBASE_TIME)

BUS_START = datetime.datetime(2025, 5, 8, 15, tzinfo=MOONBASE_TIME)
SHIFT_START = datetime.datetime(2024, 11, 8, 12, tzinfo=MOONBASE_TIME)
OMEGA_START = datetime.datetime(2024, 11, 15, 10, tzinfo=MOONBASE_TIME)
BUS_END = datetime.datetime(2024, 11, 15, 14, tzinfo=MOONBASE_TIME)

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
SHIFTS: List[str] = ["Alpha Flight", "Night Watch", "Zeta", "Dawn Guard", "Omega"]
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

    async def message(self) -> str:
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
        times: int

        if now > OMEGA_START:
            omega_diff: datetime.timedelta = now - OMEGA_START
            times = omega_diff.seconds
            return f"We are {times // 3600}:{(times//60%60):02}:{(times%60):02} into Omega, may the Bus protect us!"
        else:
            shift = diff.seconds // (6 * 3600)
            times = diff.seconds - shift * 6 * 3600

        date: int = diff.days

        shift_name = SHIFTS[shift % 4]
        time_str = f"{times // 3600}:{(times//60%60):02}:{(times%60):02}"

        total_shift = 4 * date + shift + 1
        suffix: str = (
            SUFFIX[total_shift % 10]
            if total_shift % 10 < len(SUFFIX) and not (10 < total_shift < 13)
            else "th"
        )

        return f"It is {time_str} on {shift_name}, the {total_shift}{suffix} of Bus"


class March(bot.commands.SimpleCommand):
    """Gets the current date in March 2020"""

    def __init__(self, command: str = "march") -> None:
        super().__init__(command)

    async def message(self) -> str:
        now: datetime.datetime = datetime.datetime.now(MOONBASE_TIME)

        date: int = (now - MARCH_START).days + 1
        month: str = "March"
        dow: str = WEEKDAYS[now.weekday()]

        suffix: str = (
            SUFFIX[date % 10] if date % 10 < len(SUFFIX) and not (10 < date < 13) else "th"
        )

        return f"Today is {dow}, {date}{suffix} of {month} 2020"


class WhenMarch(bot.commands.ParamCommand):
    """Finds a day in March 2020"""

    def __init__(self, command: str = "whenmarch") -> None:
        super().__init__(command, 1, 1)

    async def process_args(self, context: bot.commands.MessageContext, *args: str) -> bool:
        try:
            days = int(args[0])
        except ValueError:
            return False

        # days - 1 here because March 1st is 0 days after March 1st
        target = MARCH_START + datetime.timedelta(days=days - 1)
        date = target.date().strftime("%a, %d %b %Y")

        await context.reply_all(f"March {days} falls on {date} in the Gregorian calendar")

        return True


class BusStop(bot.commands.SimpleCommand):
    def __init__(self, session: aiohttp.ClientSession) -> None:
        super().__init__("busstop")
        self.session = session

    @staticmethod
    def hours(amount: float) -> float:
        return math.log(amount + 14.2857, 1.07) - math.log(15.2857, 1.07) + 1

    async def message(self) -> str:
        request = await self.session.get("https://pubsub.pubnub.com/history/sub-cbd7f5f5-1d3f-11e2-ac11-877a976e347c/total:RZZQRDQNLNLW/0/1")
        data = await request.json()
        amount = data[0]
        hours = BusStop.hours(amount)

        end = time.mktime(BUS_START.utctimetuple())
        end += round(3600 * hours)
        end = int(end)

        return f"The next bus stop on the time table is <t:{end}:R>!"
