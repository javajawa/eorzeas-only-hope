#!/usr/bin/python3

"""Utilities for defining bot commands"""

from __future__ import annotations

import time
from typing import Callable, Optional

import abc


class MessageContext(abc.ABC):
    """Context information for a message to allow replies."""

    @abc.abstractmethod
    async def reply_direct(self, message: str) -> None:
        """Reply directly to the user who sent this message."""

    @abc.abstractmethod
    async def reply_all(self, message: str) -> None:
        """Reply to the channel this message was received in"""

    @abc.abstractmethod
    async def react(self) -> None:
        """React to the message, indicating successful processing."""


class Command(abc.ABC):
    """Abstract command for the bot to process."""

    @abc.abstractmethod
    def matches(self, message: str) -> bool:
        """Check if this command is matched"""

    @abc.abstractmethod
    async def process(self, context: MessageContext, message: str) -> bool:
        """Handle the command in the message"""


class SimpleCommand(Command):
    """A command with no arguments which returns a string."""

    _command: str
    _action: Callable[[], Optional[str]]

    def __init__(self, command: str, action: Callable[[], Optional[str]]):
        self._command = "!" + command.strip().lower()
        self._action = action  # type: ignore

    def matches(self, message: str) -> bool:
        """Check if this command is matched"""
        return message.lower() == self._command or message.lower().startswith(
            self._command + " "
        )

    async def process(self, context: MessageContext, message: str) -> bool:
        """Handle the command in the message"""
        message = self._action()  # type: ignore

        if message is None:
            return False

        await context.reply_all(message)

        return True


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
