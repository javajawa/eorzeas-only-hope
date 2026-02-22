# SPDX-FileCopyrightText: 2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""Self care commands"""

from __future__ import annotations as _future_annotations

import datetime
import pathlib
import zoneinfo

import bot.commands
from commands.desertbus import MARCH_START, MOONBASE_TIME, SUFFIX, WEEKDAYS


class Time(bot.commands.ParamCommand):
    """Gets the current time in a timezone"""

    cache: dict[str, zoneinfo.ZoneInfo | None]
    root: pathlib.Path

    def __init__(self) -> None:
        super().__init__("now", 1, 1)

        self.cache = {}
        self.root = pathlib.Path("/usr/share/zoneinfo")

    def command_hint(self) -> str:
        return "!now [timezone, e.g. Canada/Vancouver]"

    async def process_args(self, context: bot.commands.MessageContext, *args: str) -> bool:
        """Process the command with its arguments"""

        try:
            zone = zoneinfo.ZoneInfo(args[0])
        except zoneinfo.ZoneInfoNotFoundError:
            potential = self.root / args[0]
            potential.resolve()

            await context.reply_all("Timezone not found: " + args[0])
            return True

        now = datetime.datetime.now(zone).time().isoformat(timespec="minutes")
        await context.reply_all("Time in " + args[0] + " is " + now)
        return True

    def _get_zone(self, zone_name: str) -> zoneinfo.ZoneInfo | None:
        if zone_name in self.cache:
            return self.cache[zone_name]

        try:
            zone = zoneinfo.ZoneInfo(zone_name)
            self.cache[zone_name] = zone
            return zone

        except zoneinfo.ZoneInfoNotFoundError:
            self.cache[zone_name] = None
            return None


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
