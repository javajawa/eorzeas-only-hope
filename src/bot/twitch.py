#!/usr/bin/env python3
# vim: ts=4 expandtab

"""The Twitch Bot"""

from __future__ import annotations

from typing import List

import twitchio.dataclasses  # type: ignore
from twitchio.ext import commands  # type: ignore

from bot.commands import Command, MessageContext
from .basebot import BaseBot


# noinspection PyAbstractClass
class TwitchBot(commands.Bot, BaseBot):
    """The Twitch Bot"""

    def __init__(
        self,
        token: str,
        nick: str,
        _commands: List[Command],
        channels: List[str],
    ):
        commands.Bot.__init__(
            self, irc_token=token, nick=nick, prefix="!", initial_channels=channels
        )
        BaseBot.__init__(self, _commands)

    async def event_ready(self) -> None:
        """When the Twitch bot connected."""
        print(f"Twitch Bot ready (user={self.nick})")

    async def event_message(self, message: twitchio.dataclasses.Message) -> None:
        """When the Twitch bot receives a message."""
        await self.process(TwitchMessageContext(message), message.content)


class TwitchMessageContext(MessageContext):
    """Twitch message context."""

    _message: twitchio.dataclasses.Message

    def __init__(self, message: twitchio.dataclasses.Message):
        self._message = message

    async def reply_direct(self, message: str) -> None:
        """Reply directly to the user who sent this message."""
        raise NotImplementedError()

    async def reply_all(self, message: str) -> None:
        """Reply to the channel this message was received in"""
        await self._message.channel.send(message)

    async def react(self) -> None:
        """React to the message, indicating successful processing."""
        raise NotImplementedError()

    def sender(self) -> str:
        return str(self._message.author.name)

    def channel(self) -> str:
        return str(self._message.channel)
