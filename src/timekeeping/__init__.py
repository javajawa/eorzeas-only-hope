#!/usr/bin/python3
# vim: ts=4 expandtab

"""Self care commands"""

from __future__ import annotations
from typing import List

import datetime

import bot.commands


MOONBASE_TIME = datetime.timezone(-datetime.timedelta(hours=8), "Canada/Pacific")
BUS_START = datetime.datetime(2020, 11, 13, 12, tzinfo=MOONBASE_TIME)
MARCH_START = datetime.datetime(2020, 3, 1, 0, tzinfo=MOONBASE_TIME)

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


class BusIsComing(bot.commands.SimpleCommand):
    """Count down to Desert Bus (in Desert Bus Points"""

    def __init__(self) -> None:
        super().__init__("bus", self.message)

    @staticmethod
    def message() -> str:
        now: datetime.datetime = datetime.datetime.now(MOONBASE_TIME)

        if now < BUS_START:
            points: float = (BUS_START - now).total_seconds() / (8 * 3600 + 7 * 60)

            return f"Bus Is Coming. Auto-James must acquire {points} more points to summon The Bus."

        diff: datetime.timedelta = now - BUS_START

        date: int = diff.days + 1
        shift: int = diff.seconds // (6 * 3600)
        time: int = diff.seconds - shift * 6 * 3600

        shift_name = SHIFTS[shift % 4]
        time_str = "%d:%02d:%02d" % (time // 3600, time // 60 % 60, time % 60)

        print(diff, date, shift_name, time_str)

        suffix: str = (
            SUFFIX[date % 10]
            if date % 10 < len(SUFFIX) and not (10 < date < 13)
            else "th"
        )

        return f"It is {time_str} on {shift_name}, {date}{suffix} of Bus"


class March(bot.commands.SimpleCommand):
    """Gets the current date in March 2020"""

    def __init__(self) -> None:
        super().__init__("march", self.message)

    @staticmethod
    def message() -> str:
        now: datetime.datetime = datetime.datetime.now(MOONBASE_TIME)
        date: int = (now - MARCH_START).days + 1
        dow: str = WEEKDAYS[now.weekday()]

        suffix: str = (
            SUFFIX[date % 10]
            if date % 10 < len(SUFFIX) and not (10 < date < 13)
            else "th"
        )

        return f"Today is {dow}, {date}{suffix} of March"
