#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""Commands specifically for the sugarsh0t twitch channel"""

from __future__ import annotations

import abc
import random
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


class Plan(TwitchCommand):
    def matches(self, message: str) -> bool:
        return message.startswith("!plan")

    async def respond(self, context: bot.commands.MessageContext, message: str) -> bool:
        await context.reply_all(
            random.choice(
                [
                    "Julie attempts to play NUTS (without breaking TOS)",
                    "Nuts! The squirrels are at it again",
                    "We're squirrelling away our notes on squirrels",
                    (
                        "We're playing a character with low expectations who is "
                        "sent to study some nuts-having beasts."
                    ),
                ]
            )
        )

        # "This !plan is important. "
        # "We consider ourselves a power culture. "
        # "This is not a place of Endwalker. "
        # "No critically acclaimed MMORPG is hosted here. "
        # "Nothing FFXIV is here. "
        # "This message is a warning of danger; "
        # "a danger in a particular location…"
        # "at the front of the login queue. "
        # "What is there is bunbois and catgirls. "
        # "It only unleashes if you disturb the queue. "
        # "This queue is best shunned and left empty."
        return True


class Warnings(TwitchCommand):
    def matches(self, message: str) -> bool:
        return message.startswith("!warnings") or message.startswith("!content")

    async def respond(self, context: bot.commands.MessageContext, message: str) -> bool:
        await context.reply_all("There are currently no content warnings for 'Carto'")

        return True


class SassPlan(bot.commands.Command):
    async def process(self, context: bot.commands.MessageContext, message: str) -> bool:
        if self._matches(context, message):
            await context.reply_all(
                "This ain't a Serge stream, @" + context.sender().split(":")[0]
            )
            return True

        return False

    def _matches(self, context: bot.commands.MessageContext, message: str) -> bool:
        if isinstance(context, TwitchMessageContext):
            if str(context.channel()) != "sugarsh0t":
                return False

        return self.matches(message)

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
