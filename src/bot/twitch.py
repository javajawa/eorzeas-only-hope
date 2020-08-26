#!/usr/bin/python3
# vim: ts=4 expandtab nospell

from __future__ import annotations

from typing import List, Type

import math

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
        prefixes = [
            "!",
            f"{nick.lower()}:",
            nick.lower(),
            f"@{nick.lower()}:",
            f"@{nick.lower()}",
        ]

        super().__init__(
            irc_token=token, nick=nick, prefix=prefixes, initial_channels=channels,
        )

        self.storage = storage
        self.calls = 0

    async def event_ready(self: Type[TwitchBot]):
        print(f"Twitch Bot ready (user={self.nick})")

    async def event_message(self, message):
        result = await self.handle_commands(message)

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

    @commands.command(name="pillars")
    async def pillars(self, ctx) -> None:
        data = ctx.message.content.split()
        data = data[1:]

        length = int(data[0])
        width = int(data[1]) if len(data) > 1 else 1

        if length < 3:
            return

        if width >= length:
            return

        valid = []

        for gap in range(width + 1, math.ceil(length / 2 - width)):
            count = math.ceil(length / gap)
            print(f"Checking {count} pillars of {gap - width}+{width} filling {length}")
            print(f" > calculated length is {count * gap - width}")

            if count * gap - width == length:
                valid.append(f"{count - 1} pillars {gap - width} blocks apart")

            if count % 2 == 1 and count * gap - width == length - 1:
                valid.append(f"{count - 1} pillars {gap - width} blocks apart, with extra centre block")

        if not valid:
            await ctx.send(f"No complete solutions for pillars of width {width} spanning {length}")
            return

        await ctx.send(f"For pillars of {width} blocks spanning {length} blocks: {'; '.join(valid)}")

    def run(self: Type[TwitchBot]) -> None:
        print("Running twitch bot")
        super().run()
