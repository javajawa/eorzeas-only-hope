# SPDX-FileCopyrightText: 2025 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations as _future_annotations

from typing import ClassVar

import asyncio
import logging
import random

import discord

from bot.commands import Command, MessageContext
from bot.discord import DiscordMessageContext


class Curling:
    """Allows users to throw a stone down an empty curling sheet."""

    _logger: ClassVar[logging.Logger] = logging.getLogger("curling")
    _base: ClassVar[str] = "\n" + (":ice_cube:" * 2) + ":green_heart:" + (":ice_cube:" * 13)

    _message: discord.PartialMessage
    _position: float
    _speed: float

    def __init__(self, message: discord.PartialMessage, speed: float) -> None:
        """Allows users to throw a stone down an empty curling sheet."""

        self._position = 70.0
        self._speed = speed
        self._message = message

    async def play(self) -> None:
        while self._speed >= 0.5 and self._position >= 0:
            await self._message.edit(content=self._text(self._position, self._speed))
            self._position -= self._speed
            self._speed *= 0.95
            await asyncio.sleep(0.75)

        score = str(round(abs(self._position - 11.5), 2))
        await self._message.edit(content=self._text(self._position, 0, prefix=score))

    def _text(self, position: float, speed_indicator: float, prefix: str = ".") -> str:
        if position < 0:
            return ":x: (Overshot)" + self._base

        return (
            prefix
            + "\n."
            + (" " * round(position))
            + ":curling_stone:"
            + ("~" * round(speed_indicator))
            + self._base
        )


class CurlingCommand(Command):
    """Allows users to throw a stone down an empty curling sheet."""

    _tasks: set[asyncio.Task[None]]

    def __init__(self) -> None:
        self._tasks = set()

    @property
    def command_hint(self) -> str | None:
        return "!curl"

    @property
    def group(self) -> str | None:
        return "Interactive"

    def matches(self, message: str) -> bool:
        return message in {"!curl"}

    async def process(self, context: MessageContext, _: str) -> bool:
        if not isinstance(context, DiscordMessageContext):
            return False

        apple = await context.reply_all(":curling_stone:")
        speed = random.gauss(3.405, 0.3) + random.uniform(-0.2, 0.2)

        player = Curling(apple, speed=speed)
        task = asyncio.get_running_loop().create_task(player.play())
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

        return True
