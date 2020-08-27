#!/usr/bin/python3
# vim: ts=4 expandtab

"""Abstract bot, with command processing."""

from __future__ import annotations

from typing import List

import abc
import time
import re

from bot.commands import Command, MessageContext


class BaseBot(abc.ABC):
    """Abstract bot, with command processing."""

    _commands: List[Command]
    _wasshoi: re.Pattern  # type: ignore
    _last_wasshoi: float

    def __init__(self: BaseBot, commands: List[Command]):
        self._commands = commands
        self._wasshoi = re.compile("^[^\\w]*w+h*a+s+h+o+i+([^\\w]+|$)", re.IGNORECASE)
        self._last_wasshoi = 0.0

    async def process(self: BaseBot, ctx: MessageContext, message: str) -> None:
        """Process an incoming message"""

        if self._wasshoi.search(message):
            await self.wasshoi(ctx)
            return

        for command in self._commands:
            if command.matches(message):
                if await command.process(ctx, message):
                    return

    async def wasshoi(self, ctx: MessageContext) -> None:
        """Praise in the way of the Namazu"""
        now = time.time()

        if (now - self._last_wasshoi) < 15:
            return

        await ctx.reply_all("Wasshoi!")

        self._last_wasshoi = now
