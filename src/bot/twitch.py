#!/usr/bin/python3
# vim: ts=4 expandtab nospell

from __future__ import annotations

from typing import List, Type

from twitchio.ext import commands  # type: ignore

from storage import DataStore
from eorzea import get_single_quote, get_party_quote


class TwitchBot(commands.Bot):
    storage: DataStore
    calls: int

    def __init__(
        self: Type[TwitchBot],
        token: str,
        nick: str,
        storage: DataStore,
        channels: List[str],
    ):
        super().__init__(
            irc_token=token, nick=nick, prefix="!", initial_channels=channels,
        )

        self.storage = storage
        self.calls = 0

    async def event_ready(self: Type[TwitchBot]):
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
        self.calls += 1
        names = tuple(self.storage.random() for _ in range(4))

        await ctx.send(get_party_quote(names))

    @commands.command(name="stats")
    async def show_stats(self, ctx) -> None:
        await ctx.send(f"Omega has tested {self.calls} of {len(self.storage)} souls")

    def run(self: Type[TwitchBot]) -> None:
        print("Running twitch bot")
        super().run()
