#!/usr/bin/env python3
# vim: ts=4 expandtab

"""Self care commands"""

from __future__ import annotations

import datetime

import bot.commands
from bot.discord import DiscordMessageContext


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
        super().__init__(
            "heresy", lambda: "Belopa is a false god! Resist! Praise Kashima!"
        )
