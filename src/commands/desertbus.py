# SPDX-FileCopyrightText: 2025 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations as _future_annotations

import asyncio
import dataclasses
import datetime
import math
import time

import aiohttp

import bot.commands
from bot.commands import MessageContext
from commands.order import get_targets

MOONBASE_TIME = datetime.timezone(-datetime.timedelta(hours=8), "Canada/Pacific")
MARCH_START = datetime.datetime(2020, 3, 1, 0, tzinfo=MOONBASE_TIME)
BUS_START = datetime.datetime(2026, 11, 14, 15, tzinfo=MOONBASE_TIME)
SHIFT_START = datetime.datetime(2026, 11, 14, 12, tzinfo=MOONBASE_TIME)
OMEGA_START = datetime.datetime(2026, 11, 21, 10, tzinfo=MOONBASE_TIME)
BUS_END = datetime.datetime(2026, 11, 21, 14, tzinfo=MOONBASE_TIME)

WEEKDAYS: list[str] = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

SUFFIX: list[str] = ["th", "st", "nd", "rd"]
SHIFTS: list[str] = ["Alpha Flight", "Night Watch", "Zeta", "Dawn Guard", "Omega"]

EXPANSIONS: list[str] = [
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

DB_DONATION_PUBSUB = (
    "https://pubsub.pubnub.com/history/"
    "sub-cbd7f5f5-1d3f-11e2-ac11-877a976e347c/total:GDVQRLBPQMSG/0/1"
)


class BusIsComing(bot.commands.SimpleCommand):
    """Count down to Desert Bus (in Desert Bus Points"""

    def __init__(self) -> None:
        super().__init__("bus")

    @property
    def group(self) -> str:
        return "Desert Bus"

    async def message(self) -> str:
        now: datetime.datetime = datetime.datetime.now(MOONBASE_TIME)

        if now < BUS_START:
            return pre_bus_message(now)

        if now > BUS_END:
            return post_bus_message()

        if now > OMEGA_START:
            return omega_message(now)

        diff: datetime.timedelta = now - SHIFT_START
        times: int

        shift = diff.seconds // (6 * 3600)
        times = diff.seconds - shift * 6 * 3600

        date: int = diff.days

        shift_name = SHIFTS[shift % 4]
        time_str = f"{times // 3600}:{(times // 60 % 60):02}:{(times % 60):02}"

        total_shift = 4 * date + shift + 1
        suffix: str = (
            SUFFIX[total_shift % 10]
            if total_shift % 10 < len(SUFFIX) and not (10 < total_shift < 13)
            else "th"
        )

        return f"It is {time_str} on {shift_name}, the {total_shift}{suffix} of Bus"


def post_bus_message() -> str:
    return (
        "Typical! You wait all year for a bus, "
        "and five shifts come along at once. "
        "Whelp, have to wait until next year now."
    )


def pre_bus_message(now: datetime.datetime) -> str:
    points: float = (BUS_START - now).total_seconds() / (8 * 3600 + 2 * 60)
    s_points: str = f"{points:.1f}" if points > 1 else f"{points:.2f}"
    return f"Bus Is Coming. Auto-James must acquire {s_points} more points to summon The Bus."


def omega_message(now: datetime.datetime) -> str:
    omega_diff: datetime.timedelta = now - OMEGA_START
    times = omega_diff.seconds
    omega_hours: float = times // 3600
    omega_minutes: float = times // 60 % 60
    omega_seconds: float = times % 60
    return (
        f"We are {omega_hours}:{omega_minutes:02}:{omega_seconds:02} "
        "into Omega, may the Bus protect us!"
    )


class BusStop(bot.commands.SimpleCommand):
    def __init__(self, session: aiohttp.ClientSession) -> None:
        super().__init__("busstop")
        self.session = session

    @property
    def group(self) -> str:
        return "Desert Bus"

    @staticmethod
    def hours(amount: float) -> float:
        return math.log(amount + 14.2857, 1.07) - math.log(15.2857, 1.07) + 1

    async def message(self) -> str:
        request = await self.session.get(DB_DONATION_PUBSUB)
        data = await request.json(content_type="text/javascript")
        amount = data[0]
        hours = BusStop.hours(amount)

        end = time.mktime(BUS_START.utctimetuple())
        end += round(3600 * hours)
        end = int(end)

        return f"The next bus stop on the time table is <t:{end}:R>!"


class DesertBusOrder(bot.commands.SimpleCommand):
    session: aiohttp.ClientSession

    def __init__(self, session: aiohttp.ClientSession) -> None:
        super().__init__("busorder")
        self.session = session

    @property
    def group(self) -> str:
        return "Desert Bus"

    async def message(self) -> str:
        request = await self.session.get(DB_DONATION_PUBSUB)
        data = await request.json(content_type="text/javascript")
        amount = data[0]
        amount = round(100 * amount)

        target = get_targets(amount, amount)
        targets = [x.div(100, amount / 100) for x in target]

        # Show three at most.
        targets = targets[0:3]
        targets.sort(key=lambda a: a.total)

        return "Donate " + ", or ".join([str(t) for t in targets])
