#!/usr/bin/python3
# vim: ts=4 expandtab

from __future__ import annotations

from typing import Type

import re
import discord

from storage import DataStore


class DiscordBot(discord.Client):
    storage: DataStore
    pattern: re.Pattern

    def __init__(self: Type[DiscordBot], storage: DataStore):
        super().__init__()

        self.storage = storage
        self.pattern = re.compile(' you[^ ]*( are)? [^ ]+zea\'?s only hope', re.IGNORECASE)

    async def on_ready(self: DiscordBot):
        print('%s has connected to Discord!' % self.user)

    async def on_message(self: Type[DiscordBot], message: discord.Message) -> None:
        if message.author == self.user:
            return

        if message.content == '!onlyhope':
            await self.send_champion(message.channel)
            return

        for line in message.content.split('\n'):
            name: str = ''

            if self.pattern.search(line):
                [name, _] = message.content.split(' you', 1)
            elif message.content.startswith('!onlyhope'):
                name = message.content[9:]

            # TODO: remove all punctuation etc?
            name = name.strip()

            if name:
                print('Adding %s from %s::%s' % (
                    name, message.channel.guild.name, message.channel.name))

                if self.storage.add(name):
                    print('Adding reaction')
                    await message.add_reaction('\U0001F44D')

    async def send_champion(self: DiscordBot, channel: discord.TextChannel):
        name = self.storage.random()

        await channel.send('**%s**, you\'re Eorzea\'s Only Hope!' % name)
