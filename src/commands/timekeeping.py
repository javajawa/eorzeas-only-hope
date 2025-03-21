# SPDX-FileCopyrightText: 2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""Self care commands"""

from __future__ import annotations as _future_annotations

import datetime

import bot.commands
from commands.desertbus import MARCH_START, MOONBASE_TIME, SUFFIX, WEEKDAYS


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
