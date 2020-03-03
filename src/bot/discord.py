#!/usr/bin/python3
# vim: ts=4 expandtab

# from __future__ import annotations

from typing import Type 

import discord

from storage import DataStore

class DiscordBot(discord.Client):
    def __init__(self: Type['EorzeasOnlyHopeBot'], storage: DataStore):
        super().__init__()

        self.storage = storage

    async def on_ready(self):
        print('%s has connected to Discord!' % self.user)

    async def on_message(message: discord.Message):
        if message.author == client.user:
            return

        if message.contents == '!onlyhope':
            await self.send_champion(message.channel)
            return

        for line in message.contents.split('\n'):
            if not r' you[^ ]*( are)?[^ ]+zea\'?s only hope'.test(message.contents):
                return

            [name, _] = message.contents.split(' you', 1)
            # TODO: remove all punctuation
            name = name.strip()

            print('Adding %s from %s::%s' % (name, channel.guild.name, channel.name))
            self.storage.add(name)

    async def send_champion(channel: discord.TextChannel):
        name = self.storage.random()

        await channel.send('**%s**, you\'re Eorzea\'s Only Hope!' % name)  
