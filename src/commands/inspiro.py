# SPDX-FileCopyrightText: 2025 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations as _future_annotations

from typing import NamedTuple

import asyncio

import aiohttp
import discord

from bot.commands import Command, MessageContext
from bot.discord import DiscordMessageContext


class InspireContext(NamedTuple):
    source_message: DiscordMessageContext
    image_options: tuple[str, str, str]


class InspiroBot(Command):
    """Grab a selection of random images from Inspiro-Bot, allowing a user to pick one."""

    _session: aiohttp.ClientSession
    _cache: dict[int, InspireContext]

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session
        self._cache = {}

    @property
    def command_hint(self) -> str | None:
        return "!inspire"

    @property
    def group(self) -> str | None:
        return "Interactive"

    def matches(self, message: str) -> bool:
        return message.strip() in {"!inspire", "!inspiro"}

    async def process(self, context: MessageContext, _: str) -> bool:
        """Handle the command in the message"""

        if not isinstance(context, DiscordMessageContext):
            return False

        channel = context.message.channel

        if isinstance(channel, discord.DMChannel):
            await context.reply_all(await self.get_image())
            return True

        if not isinstance(channel, discord.TextChannel):
            return False

        urls = await asyncio.gather(self.get_image(), self.get_image(), self.get_image())

        try:
            message: discord.Message = await context.reply_direct("\n".join(urls))
        except discord.errors.Forbidden:
            await context.reply_all(f"Oi, {context.sender()}, your DMs aren't open.")
            return True

        self._cache[message.id] = InspireContext(context, urls)

        await message.add_reaction("1️⃣")
        await message.add_reaction("2️⃣")
        await message.add_reaction("3️⃣")
        await message.add_reaction("♻️")

        return True

    async def handle_reaction(self, event: discord.RawReactionActionEvent) -> None:
        if event.message_id not in self._cache:
            return

        if event.emoji.name == "♻️":
            await self.process(self._cache[event.message_id].source_message, "")
            del self._cache[event.message_id]
            return

        index = {"1️⃣": 0, "2️⃣": 1, "3️⃣": 2}.get(event.emoji.name)

        if index is None:
            return

        context = self._cache[event.message_id]
        image = str(self._cache[event.message_id].image_options[index])

        await context.source_message.message.reply(image, mention_author=False)
        del self._cache[event.message_id]

    async def get_image(self) -> str:
        response = await self._session.get("https://inspirobot.me/api?generate=true")
        return await response.text()
