#!/usr/bin/python3
# vim: ts=4 expandtab

from __future__ import annotations

from typing import Type

from twitchio.ext import commands

from storage import DataStore


class TwitchBot(commands.Bot):
    storage: DataStore

    def __init__(self: Type[TwitchBot], token: str, client_id: int, nick: str, storage: DataStore):
        super().__init__(
            irc_token=token,
            client_id=client_id,
            nick=nick,
            prefix='!',
            initial_channels=[]
        )

        self.storage = storage
        self.command(self.send_champion, name='onlyhope')
 
    async def send_champion(self, ctx):
        name = self.storage.random()
        await ctx.send('**%s**, you\'re Eorzea\'s Only Hope!' % name)

    async def join(self: Type[TwitchBot], channel: str) -> bool:
        return self.join_channels([channel])

    def run(self: Type[TwitchBot]) -> None:
        print("Running twitch bot")
        super().run()
