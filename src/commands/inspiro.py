# SPDX-FileCopyrightText: 2025 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations as _future_annotations

import asyncio

import aiohttp
import discord

from bot.commands import Command, MessageContext
from bot.discord import DiscordMessageContext


class InspiroBot(Command):
    """Grab a selection of random images from Inspiro-Bot, allowing a user to pick one."""

    _session: aiohttp.ClientSession
    _cache: dict[int, tuple[MessageContext, discord.TextChannel, str, str, str]]

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

        await message.add_reaction("1️⃣")
        await message.add_reaction("2️⃣")
        await message.add_reaction("3️⃣")
        await message.add_reaction("♻️")

        self._cache[message.id] = (context, channel, *urls)
        return True

    async def handle_reaction(self, event: discord.RawReactionActionEvent) -> None:
        if event.message_id not in self._cache:
            return

        if event.emoji.name == "♻️":
            await self.process(self._cache[event.message_id][0], "")
            del self._cache[event.message_id]
            return

        index = {"1️⃣": 2, "2️⃣": 3, "3️⃣": 4}.get(event.emoji.name)

        if not index:
            return

        target = self._cache[event.message_id][1]
        image = str(self._cache[event.message_id][index])

        await target.send(image)
        del self._cache[event.message_id]

    async def get_image(self) -> str:
        response = await self._session.get("https://inspirobot.me/api?generate=true")
        return await response.text()
