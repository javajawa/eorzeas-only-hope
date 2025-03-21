# SPDX-FileCopyrightText: 2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""The Twitch Bot"""

from __future__ import annotations as _future_annotations

import asyncio
import logging

import twitchio  # type: ignore[import-untyped]
from twitchio.ext import commands  # type: ignore[import-untyped]

from bot.commands import Command, MessageContext

from .basebot import BaseBot


# noinspection PyAbstractClass
class TwitchBot(commands.Bot, BaseBot):  # type: ignore[misc]
    """The Twitch Bot"""

    def __init__(  # pylint: disable=R0917
        self,
        loop: asyncio.AbstractEventLoop,
        logger: logging.Logger,
        token: str,
        nick: str,
        _commands: list[Command],
        channels: list[str],
    ) -> None:
        commands.Bot.__init__(
            self,
            loop=loop,
            token=token,
            nick=nick,
            prefix="!",
            initial_channels=channels,
        )
        BaseBot.__init__(self, logger, _commands)

    async def event_ready(self) -> None:
        """When the Twitch bot connected."""
        self._logger.info("Twitch Bot ready (user=%s)", self.nick)

    async def event_message(self, message: twitchio.Message) -> None:
        """When the Twitch bot receives a message."""
        if not message.author or message.author.name == self.nick:
            return

        await self.process(TwitchMessageContext(message), message.content)


class TwitchMessageContext(MessageContext):
    """Twitch message context."""

    _message: twitchio.Message

    def __init__(self, message: twitchio.Message) -> None:
        self._message = message

    async def reply_direct(self, message: str) -> None:
        """Reply directly to the user who sent this message."""
        raise NotImplementedError

    async def reply_all(self, message: str) -> None:
        """Reply to the channel this message was received in"""
        await self._message.channel.send(message)

    async def react(self) -> None:
        """React to the message, indicating successful processing."""
        raise NotImplementedError

    def sender(self) -> str:
        return str(self._message.author.name)

    def channel(self) -> str:
        return str(self._message.channel.name)
