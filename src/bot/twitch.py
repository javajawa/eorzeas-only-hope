#!/usr/bin/python3
# vim: ts=4 expandtab nospell

from __future__ import annotations

from typing import Any, List, Type

from twitchio.ext import commands  # type: ignore

from storage import DataStore
from eorzea import get_single_quote
from .basebot import BaseBot


class TwitchBot(commands.Bot, BaseBot):
    def __init__(
        self,
        token: str,
        nick: str,
        storage: DataStore,
        channels: List[str],
    ):
        prefixes = [
            "!",
            f"{nick.lower()}:",
            nick.lower(),
            f"@{nick.lower()}:",
            f"@{nick.lower()}",
        ]

        commands.Bot.__init__(
            self,
            irc_token=token,
            nick=nick,
            prefix=prefixes,
            initial_channels=channels,
        )
        BaseBot.__init__(self, storage)

        self.storage = storage
        self.calls = 0

    async def event_ready(self: Type[TwitchBot]) -> None:
        print(f"Twitch Bot ready (user={self.nick})")

    async def event_message(self, message):
        await self.handle_commands(message)

    @commands.command(name="onlyhope")
    async def send_champion(self, ctx):
        self.calls += 1
        name = self.storage.random()

        await ctx.send(get_single_quote(name))

    @commands.command(name="party")
    async def send_party(self, ctx):
        await self.party_command(ctx.message.content, ctx)

    @commands.command(name="stats")
    async def show_stats(self, ctx) -> None:
        await self.show_stats(ctx)

    @commands.command(name="pillars")
    async def pillars(self, ctx) -> None:
        await self.pillars_command(ctx.message.content, ctx)

    def run(self: Type[TwitchBot]) -> None:
        print("Running twitch bot")
        super().run()

    async def reply_all(self: BaseBot, ctx: Any, message: str) -> None:
        await ctx.send(message)

    async def react(self: BaseBot, ctx: Any) -> None:
        pass
