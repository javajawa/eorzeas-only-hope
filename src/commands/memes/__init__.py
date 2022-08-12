#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""Self care commands"""

from __future__ import annotations

import datetime
import requests

import bot.commands
from bot.discord import DiscordMessageContext

from .order import TeamOrder, TeamOrderDonate, TeamOrderBid, DesertBusOrder

MOONBASE_TIME = datetime.timezone(-datetime.timedelta(hours=8), "Canada/Pacific")


class Belopa(bot.commands.SimpleCommand):
    """Praise Belopa (if it is Night Watch or Omega)"""

    def __init__(self) -> None:
        super().__init__("belopa", lambda: "")

    async def process(self, context: bot.commands.MessageContext, message: str) -> bool:
        now: datetime.datetime = datetime.datetime.now(MOONBASE_TIME)

        if now.hour >= 18:
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
        super().__init__("heresy", lambda: "Belopa is a false god! Resist! Praise Kashima!")


class InspiroBot(bot.commands.SimpleCommand):
    """Grab a random image from Inspiro-Bot"""

    def __init__(self) -> None:
        super().__init__("inspire", InspiroBot.message)

    @staticmethod
    def message() -> str:
        return requests.get(url="https://inspirobot.me/api?generate=true").text


class Beep(bot.commands.SimpleCommand):
    """Do a boop"""

    def __init__(self) -> None:
        super().__init__("beep", lambda: "*boop*!")


class Boop(bot.commands.SimpleCommand):
    """Do a beep"""

    def __init__(self) -> None:
        super().__init__("boop", lambda: "beep!")


__all__ = [
    "Boop",
    "Beep",
    "Heresy",
    "Belopa",
    "TeamOrder",
    "TeamOrderDonate",
    "TeamOrderBid",
    "DesertBusOrder",
]
