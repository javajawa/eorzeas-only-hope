#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""Utilities for defining bot commands"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

import abc
import re
import time


class MessageContext(abc.ABC):
    """Context information for a message to allow replies."""

    @abc.abstractmethod
    async def reply_direct(self, message: str) -> None:
        """Reply directly to the user who sent this message."""

    @abc.abstractmethod
    async def reply_all(self, message: str) -> Any:
        """Reply to the channel this message was received in"""

    @abc.abstractmethod
    async def react(self) -> None:
        """React to the message, indicating successful processing."""

    @abc.abstractmethod
    def sender(self) -> str:
        """Gets the username of the user who sent the message"""

    @abc.abstractmethod
    def channel(self) -> str:
        """Gets the channel where the message was sent"""


class Command(abc.ABC):
    """Abstract command for the bot to process."""

    @abc.abstractmethod
    def matches(self, message: str) -> bool:
        """Check if this command is matched"""

    @abc.abstractmethod
    async def process(self, context: MessageContext, message: str) -> bool:
        """Handle the command in the message"""


class SimpleCommand(Command, abc.ABC):
    """A command with no arguments which returns a string."""

    _command: str

    def __init__(self, command: str):
        self._command = "!" + command.strip().lower()

    def matches(self, message: str) -> bool:
        """Check if this command is matched"""
        return message.lower() == self._command or message.lower().startswith(
            self._command + " "
        )

    async def process(self, context: MessageContext, message: str) -> bool:
        """Handle the command in the message"""
        reply = self.message()

        if reply is None:
            return False

        await context.reply_all(reply)

        return True

    @abc.abstractmethod
    def message(self) -> Optional[str]:
        pass


class RandomCommand(Command):
    _triggers: List[str]
    _replies: List[str]
    _params: Dict[str, List[str]]

    def __init__(
        self, triggers: List[str], replies: List[str], args: Dict[str, List[str]]
    ) -> None:
        self._triggers = ["!" + trigger.strip("!") for trigger in triggers]
        self._replies = [str(x) for x in replies]
        self._params = {k: [str(x) for x in v] for k, v in args.items()}

    def matches(self, message: str) -> bool:
        return any(message.startswith(x + " ") or message == x for x in self._triggers)

    async def process(self, context: MessageContext, message: str) -> bool:
        reply_format = random.choice(self._replies)

        if not reply_format:
            return False

        args = {k: random.choice(self._params[k]) for k in self._params}

        reply = reply_format.format(**args)

        await context.reply_all(reply)
        return True


class RegexCommand(RandomCommand, abc.ABC):
    """A "command" that is a reply to a matched regexp"""

    _regexp: re.Pattern  # type: ignore

    def __init__(self, pattern: str, replies: List[str], args: Dict[str, List[str]]) -> None:
        super().__init__([], replies, args)
        self._regexp = re.compile(pattern, re.IGNORECASE)

    def matches(self, message: str) -> bool:
        """Check if this command is matched"""

        return self._regexp.search(message) is not None


class RateLimitCommand(Command):
    """Command decorator that rate limits a command"""

    _last: float = 0
    _interval: float
    _command: Command

    def __init__(self, command: Command, interval: float):
        self._command = command
        self._interval = interval

    def matches(self, message: str) -> bool:
        """Check if this command is matched"""
        return self._command.matches(message)

    async def process(self, context: MessageContext, message: str) -> bool:
        """Handle the command in the message"""
        now = time.time()

        if now - self._last < self._interval:
            return False

        self._last = now

        return await self._command.process(context, message)


class ParamCommand(Command):
    """A command with parameters"""

    _command: str
    _min_args: int
    _max_args: int

    def __init__(self, command: str, min_args: int, max_args: int):
        self._command = "!" + command.strip().lower()
        self._min_args = min_args
        self._max_args = max_args

        if self._min_args > 0:
            self._command += " "

    def matches(self, message: str) -> bool:
        """Check if this command is matched"""
        if message.lower() != self._command and not message.startswith(self._command):
            return False

        args = message.strip().split()

        count = len(args) - 1  # The command name does not count as an arg.

        return self._min_args <= count <= self._max_args

    async def process(self, context: MessageContext, message: str) -> bool:
        """Handle the command in the message"""
        args = message.strip().split()

        return await self.process_args(context, *args[1:])

    @abc.abstractmethod
    async def process_args(self, context: MessageContext, *args: str) -> bool:
        """Process the command with it's arguments"""
