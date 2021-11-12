#!/usr/bin/env python3
# vim: ts=4 expandtab

"""Self care commands"""

from __future__ import annotations
from typing import List

import datetime
import random

import bot.commands


MOONBASE_TIME = datetime.timezone(-datetime.timedelta(hours=8), "Canada/Pacific")

MARCH_START = datetime.datetime(2020, 3, 1, 0, tzinfo=MOONBASE_TIME)

BUS_START = datetime.datetime(2021, 11, 12, 10, tzinfo=MOONBASE_TIME)
SHIFT_START = datetime.datetime(2020, 11, 13, 12, tzinfo=MOONBASE_TIME)
OMEGA_START = datetime.datetime(2020, 11, 19, 22, tzinfo=MOONBASE_TIME)
BUS_END = datetime.datetime(2020, 11, 20, 6, tzinfo=MOONBASE_TIME)

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
    "",
    "Bus Is Here",
    "A Bus Reborn",
    "Desertsward",
    "Stormbus",
    "Donationbringers",
    "ForHopen",
    "The Summoning of Buslopa!",
]


class BusIsComing(bot.commands.SimpleCommand):
    """Count down to Desert Bus (in Desert Bus Points"""

    def __init__(self) -> None:
        super().__init__("bus", self.message)

    @staticmethod
    def message() -> str:
        now: datetime.datetime = datetime.datetime.now(MOONBASE_TIME)

        if now < BUS_START:
            points: float = (BUS_START - now).total_seconds() / (8 * 3600 + 2 * 60)
            s_points: str = f"{points:.1f}"

            return (
                "Bus Is Coming. "
                f"Auto-James must acquire {s_points} more points to summon The Bus."
            )

        if now > BUS_END:
            return (
                "Typical! You wait all year for a bus, "
                "and four shifts come along at once. "
                "Whelp, have to wait until next year now."
            )

        diff: datetime.timedelta = now - SHIFT_START
        shift: int
        time: int

        if now > OMEGA_START:
            omega_diff: datetime.timedelta = now - OMEGA_START
            shift = 1
            time = omega_diff.seconds
        else:
            shift = diff.seconds // (6 * 3600)
            time = diff.seconds - shift * 6 * 3600

        date: int = diff.days + 1

        shift_name = SHIFTS[shift % 4]
        time_str = f"{time // 3600}:{(time//60%60):02}:{(time%3600):02}"

        total_shift = 4 * date + shift
        suffix: str = (
            SUFFIX[total_shift % 10]
            if total_shift % 10 < len(SUFFIX) and not (10 < total_shift < 13)
            else "th"
        )

        expansion: str = ""

        if now > OMEGA_START:
            expansion = "Into The Rift"
            shift_name = "Omega"
            date = "π"  # type: ignore
            shift = "e"  # type: ignore
        else:
            expansion = EXPANSIONS[date]

        return random.choice(
            [
                f"It is {time_str} on Desert Bus XIV, {date}.{shift} {expansion} ({shift_name})",
                f"It is {time_str} on {shift_name}, the {total_shift}{suffix} of Bus",
            ]
        )


class March(bot.commands.SimpleCommand):
    """Gets the current date in March 2020"""

    def __init__(self) -> None:
        super().__init__("truemarch", self.message)

    @staticmethod
    def message() -> str:
        now: datetime.datetime = datetime.datetime.now(MOONBASE_TIME)

        date: int = (now - MARCH_START).days + 1
        month: str = "March"
        dow: str = WEEKDAYS[now.weekday()]

        suffix: str = (
            SUFFIX[date % 10] if date % 10 < len(SUFFIX) and not (10 < date < 13) else "th"
        )

        return f"Today is {dow}, {date}{suffix} of {month} 2020"


class SMarch(bot.commands.SimpleCommand):
    """Gets the current date in March 2020"""

    def __init__(self) -> None:
        super().__init__("march", self.message)

    @staticmethod
    def message() -> str:
        now: datetime.datetime = datetime.datetime.now(MOONBASE_TIME)

        date: int
        month: str

        if now < BUS_END:
            date = (now - MARCH_START).days + 1
            month = "March"
        else:
            date = (now - BUS_END).days + 1
            month = "Smarch"

        dow: str = WEEKDAYS[now.weekday()]

        suffix: str = (
            SUFFIX[date % 10] if date % 10 < len(SUFFIX) and not (10 < date < 13) else "th"
        )

        return f"Today is {dow}, {date}{suffix} of {month} 2020"
