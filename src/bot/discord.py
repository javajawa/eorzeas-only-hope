#!/usr/bin/python3
# vim: ts=4 expandtab

from __future__ import annotations

import re
from discord import Client, Message  # type: ignore

from bot.basebot import BaseBot
from storage import DataStore


class DiscordBot(Client, BaseBot):
    storage: DataStore
    pattern: re.Pattern  # type: ignore

    def __init__(self: DiscordBot, storage: DataStore):
        BaseBot.__init__(self, storage)
        Client.__init__(self)

    async def on_ready(self: DiscordBot):
        print(f"{self.user} has connected to Discord!")

    async def on_message(self: DiscordBot, message: Message) -> None:
        if message.author == self.user:
            return

        await self.process(message.content, message)

    async def reply_all(self: DiscordBot, ctx: Message, message: str) -> None:
        await ctx.channel.send(message)

    async def react(self: DiscordBot, ctx: Message) -> None:
        await ctx.add_reaction("\U0001F44D")
