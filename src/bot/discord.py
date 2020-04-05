#!/usr/bin/python3
# vim: ts=4 expandtab

from __future__ import annotations

import re
import discord  # type: ignore

from bot.basebot import BaseBot
from storage import DataStore


class DiscordBot(discord.Client, BaseBot):
    storage: DataStore
    pattern: re.Pattern  # type: ignore

    def __init__(self: DiscordBot, storage: DataStore):
        BaseBot.__init__(self, storage)
        discord.Client.__init__(self)

    async def on_ready(self: DiscordBot):
        print("%s has connected to Discord!" % self.user)

    async def on_message(self: DiscordBot, message: discord.Message) -> None:
        if message.author == self.user:
            return

        await self.process(message.content, message)

    async def reply_all(self: DiscordBot, ctx: discord.Message, message: str) -> None:
        await ctx.channel.send(message)

    async def react(self: DiscordBot, ctx: discord.Message) -> None:
        await ctx.add_reaction("\U0001F44D")
