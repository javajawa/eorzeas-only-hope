#!/usr/bin/python3
# vim: ts=4 expandtab

# from __future__ import annotations

from twitchio.ext import commands


class TwitchBot:
    def __init__(self: 'TwitchBot', token: str, id: int, nick: str):
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

    async def join(self, channel: str):
        self.bot.join_channel(channel)

    def run(self):
        print("Running twitch bot")
        self.bot.run()
