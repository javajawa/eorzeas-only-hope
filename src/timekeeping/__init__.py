#!/usr/bin/python3
# vim: ts=4 expandtab

"""Self care commands"""

from __future__ import annotations
from typing import List

import datetime
import random

import bot.commands
from bot.discord import DiscordMessageContext


MOONBASE_TIME = datetime.timezone(-datetime.timedelta(hours=8), "Canada/Pacific")

MARCH_START = datetime.datetime(2020, 3, 1, 0, tzinfo=MOONBASE_TIME)

BUS_START = datetime.datetime(2020, 11, 13, 10, tzinfo=MOONBASE_TIME)
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
            points: float = (BUS_START - now).total_seconds() / (8 * 3600 + 7 * 60)

            return f"Bus Is Coming. Auto-James must acquire {points} more points to summon The Bus."

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
        time_str = "%d:%02d:%02d" % (time // 3600, time // 60 % 60, time % 60)

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
        super().__init__("march", self.message)

    @staticmethod
    def message() -> str:
        now: datetime.datetime = datetime.datetime.now(MOONBASE_TIME)

        date: int
        month: str

        if now > BUS_END:
            date = (now - MARCH_START).days + 1
            month = "March"
        else:
            date = (now - BUS_END).days + 1
            month = "Smarch"

        dow: str = WEEKDAYS[now.weekday()]

        suffix: str = (
            SUFFIX[date % 10]
            if date % 10 < len(SUFFIX) and not (10 < date < 13)
            else "th"
        )

        return f"Today is {dow}, {date}{suffix} of {month} 2020"


class Belopa(bot.commands.SimpleCommand):
    """Praise Belopa (if it is Night Watch or Omega)"""

    def __init__(self) -> None:
        super().__init__("belopa", lambda: "")

    async def process(self, context: bot.commands.MessageContext, message: str) -> bool:
        now: datetime.datetime = datetime.datetime.now(MOONBASE_TIME)

        if now.hour >= 18 or (OMEGA_START < now < BUS_END):
            await context.reply_all("Praise Belopa!")

            if isinstance(context, DiscordMessageContext):
                await context.reply_all(
                    "https://cdn.discordapp.com/emojis/777440813063471144.png?v=1"
                )

            return True

        await context.reply_all("Belopa is a false god!")

        return True


class Heresy(bot.commands.SimpleCommand):
    """Resist the presence of Belopa"""

    def __init__(self) -> None:
        super().__init__(
            "heresy", lambda: "Belopa is a false god! Resist! Praise Kashima!"
        )
