#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""The Discord bot"""

from __future__ import annotations

import asyncio
from typing import List, Union

from discord import Client, Embed, Message, DMChannel, Reaction, User

from bot.basebot import BaseBot
from bot.commands import Command, MessageContext


class DiscordBot(Client, BaseBot):
    """The Discord bot"""

    def __init__(self: DiscordBot, loop: asyncio.AbstractEventLoop, commands: List[Command]):
        BaseBot.__init__(self, commands)
        Client.__init__(self, loop=loop)

    async def on_ready(self: DiscordBot) -> None:
        """When the bot connects."""
        print(f"{self.user} has connected to Discord!")

    async def on_message(self: DiscordBot, message: Message) -> None:
        """When a message is received."""
        if message.author == self.user:
            return

        await self.process(DiscordMessageContext(message), message.content)

    # pylint: disable=unused-argument
    async def on_reaction_add(self, reaction: Reaction, user: User) -> None:
        if reaction.message.author != self.user:
            return

        if reaction.emoji != "❌":
            return

        await reaction.message.edit(content="[Bot message removed by user request]")


class DiscordMessageContext(MessageContext):
    """Discord message context."""

    _message: Message

    def __init__(self, message: Message):
        self._message = message

    async def reply_direct(self, message: str) -> None:
        """Reply directly to the user who sent this message."""
        await self._message.author.send(message)

    async def reply_all(self, message: Union[str, Embed]) -> None:
        """Reply to the channel this message was received in"""

        if isinstance(message, Embed):
            await self._message.channel.send(embed=message)
        else:
            await self._message.channel.send(message)

    async def react(self) -> None:
        """React to the message, indicating successful processing."""
        await self._message.add_reaction("\U0001F44D")

    def sender(self) -> str:
        return str(self._message.author.name) + "#" + str(self._message.author.discriminator)

    def channel(self) -> str:
        if isinstance(self._message.channel, DMChannel):
            return "[DMs]"

        return str(self._message.channel.name)
