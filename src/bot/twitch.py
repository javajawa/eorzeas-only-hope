#!/usr/bin/python3
# vim: ts=4 expandtab

from __future__ import annotations

from typing import Type

from twitchio.ext import commands


class TwitchBot:
    def __init__(self: Type[TwitchBot], token: str, id: int, nick: str):
        self.bot = commands.Bot(
            irc_token=token,
            client_id=id,
            nick=nick,
            prefix='!',
            initial_channels=[]
        )

        @self.bot.command(name='onlyhope')
        async def send_champion(self, ctx):
            name = self.storage.random()

            await ctx.send('**%s**, you\'re Eorzea\'s Only Hope!' % name)

    async def join(self: Type[TwitchBot], channel: str) -> bool:
        return self.bot.join_channel(channel)

    def run(self: Type[TwitchBot]) -> None:
        print("Running twitch bot")
        self.bot.run()
