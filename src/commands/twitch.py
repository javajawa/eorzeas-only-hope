#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

# vim: ts=4 expandtab

"""Commands specifically for the sugarsh0t twitch channel"""

from __future__ import annotations

import abc

import bot.commands
from bot.twitch import TwitchMessageContext


class TwitchCommand(bot.commands.Command):
    async def process(self, context: bot.commands.MessageContext, message: str) -> bool:
        if not isinstance(context, TwitchMessageContext):
            return False

        if str(context.channel()) != "sugarsh0t":
            return False

        return await self.respond(context, message)

    @abc.abstractmethod
    async def respond(self, context: TwitchMessageContext, message: str) -> bool:
        pass


class Plan(TwitchCommand):
    def matches(self, message: str) -> bool:
        return message.startswith("!plan")

    async def respond(self, context: TwitchMessageContext, message: str) -> bool:
        await context.reply_all("Znjjntr! Gjhr Jhi! (see !warnings for game info)")

        return True


class Warnings(TwitchCommand):
    def matches(self, message: str) -> bool:
        return message.startswith("!warnings")

    async def respond(self, context: TwitchMessageContext, message: str) -> bool:
        await context.reply_all(
            "Content Warnings for 'What Remains of Edith Finch': This game deals entirely with death and acceptance of death. As such death of adults, children, and animals are depicted and described. This includes some scenes with animated gore, and discussion of addiction, suicide, and kidnapping."
        )

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
