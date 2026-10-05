# SPDX-FileCopyrightText: 2026 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations as _future_annotations

import asyncio
import random

import discord.abc

from bot.commands import Command, MessageContext
from bot.discord import DiscordMessageContext
from bot.twitch import TwitchMessageContext

CHEER = "KITS"


class CheerCommand(Command):
    state: int | None

    def __init__(self) -> None:
        super().__init__()
        self.state = None

    @property
    def command_hint(self) -> str | None:
        return None

    def matches(self, message: str) -> bool:
        if self.state is None:
            return message == "!cheer"

        return message.upper().rstrip("!? ") == CHEER[self.state]

    async def process(self, context: MessageContext, _: str) -> bool:
        if not isinstance(context, TwitchMessageContext):
            return False

        if str(context.channel()) != "exachixkitsune":
            return False

        self.state = 0 if self.state is None else self.state + 1

        if self.state >= len(CHEER):
            await context.reply_all("Goooooo Kits!!")
            self.state = None
            return True

        await context.reply_all("Give me a " + CHEER[self.state])
        return True


class GirlCommand(Command):
    @property
    def command_hint(self) -> str | None:
        return None

    def matches(self, message: str) -> bool:
        return message == "!girl"

    async def process(self, context: MessageContext, _: str) -> bool:
        if not isinstance(context, DiscordMessageContext):
            return False

        message = await context.message.reply("Scanning...please wait.", mention_author=False)

        author = context.message.author
        girl = self._is_girl(author)

        await asyncio.sleep(random.randrange(8, 36) / 10)
        if not girl:
            await message.edit(
                content="Girl status unclear. Please consult yourself for more information?",
            )
            return True

        await message.edit(content="Update: Girl Particles Detected. Proceeding to cuteness check")
        await asyncio.sleep(random.randrange(8, 48) / 10)
        await message.edit(content="Cute Girl Confirmed!")
        return True

    def _is_girl(self, author: discord.abc.Messageable) -> bool:
        girl: bool = False

        if hasattr(author, "nick") and author.nick:
            girl = girl or "she/her" in author.nick
            girl = girl or "she/they" in author.nick

        if hasattr(author, "name") and author.name:
            girl = girl or "she/her" in author.name
            girl = girl or "she/they" in author.name

        if hasattr(author, "roles"):
            roles = author.roles

            for role in roles:
                if role.name == "she/her":
                    girl = True
                if role.name == "she/they":
                    girl = True

        return girl
