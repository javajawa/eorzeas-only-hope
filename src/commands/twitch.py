#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""Commands specifically for the sugarsh0t twitch channel"""

from __future__ import annotations

import abc
import re

import bot.commands
from bot.twitch import TwitchMessageContext


class TwitchCommand(bot.commands.Command):
    async def process(self, context: bot.commands.MessageContext, message: str) -> bool:
        if isinstance(context, TwitchMessageContext):
            if str(context.channel()) != "sugarsh0t":
                return False

        return await self.respond(context, message)

    @abc.abstractmethod
    async def respond(self, context: bot.commands.MessageContext, message: str) -> bool:
        pass


class SassPlan(TwitchCommand):
    async def respond(self, context: bot.commands.MessageContext, message: str) -> bool:
        user = "@" + context.sender()

        await context.reply_all("This ain't a Serge stream, " + user)
        return True

    def matches(self, message: str) -> bool:
        return (
            message.startswith("!sassplan")
            or message.startswith("!flan")
            or message.startswith("!phlan")
            or message.startswith("!cheesecake")
            or message.startswith("!sassflan")
            or message.startswith("!sasscheesecake")
            or message.startswith("!sassfondue")
            or message.startswith("!sassphlan")
        )


class Cardinal(TwitchCommand):
    def __init__(self) -> None:
        self.regexp = re.compile("^!(north|east|south|west)+($| )")

    def matches(self, message: str) -> bool:
        return bool(self.regexp.match(message))

    async def respond(self, context: bot.commands.MessageContext, message: str) -> bool:
        await context.reply_all("East... always into the East!")
        return True
