#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""Abstract bot, with command processing."""

from __future__ import annotations

from typing import List

import abc
import logging

from bot.commands import Command, MessageContext


class BaseBot(abc.ABC):
    """Abstract bot, with command processing."""

    _logger: logging.Logger
    _commands: List[Command]

    def __init__(self: BaseBot, logger: logging.Logger, commands: List[Command]):
        self._logger = logger
        self._commands = commands

    async def process(self: BaseBot, ctx: MessageContext, message: str) -> None:
        """Process an incoming message"""

        for command in self._commands:
            if command.matches(message):
                async with ctx.typing():
                    try:
                        self._logger.debug("Running %s", command)
                        if await command.process(ctx, message):
                            return
                    except BaseException as ex:
                        self._logger.error("Error in command %s", command, exc_info=ex)

    def __str__(self) -> str:
        return str(self)
