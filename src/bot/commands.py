# SPDX-FileCopyrightText: 2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""Utilities for defining bot commands"""

from __future__ import annotations as _future_annotations

from types import TracebackType
from typing import Protocol, runtime_checkable

import abc
import asyncio
import time
from contextlib import AbstractAsyncContextManager

import discord


class MessageContext(abc.ABC):
    """Context information for a message to allow replies."""

    @abc.abstractmethod
    async def reply_direct(self, message: str) -> object | None:
        """Reply directly to the user who sent this message."""

    @abc.abstractmethod
    async def reply_all(self, message: str) -> object | None:
        """Reply to the channel this message was received in"""

    @abc.abstractmethod
    async def react(self) -> None:
        """React to the message, indicating successful processing."""

    def typing(self) -> AbstractAsyncContextManager[None]:
        """React to the message, indicating successful processing."""
        return BlankContextManager()

    @abc.abstractmethod
    def sender(self) -> str:
        """Gets the username of the user who sent the message"""

    @abc.abstractmethod
    def channel(self) -> str:
        """Gets the channel where the message was sent"""


class Command(abc.ABC):
    """Abstract command for the bot to process."""

    @property
    def group(self) -> str | None:
        return None

    @property
    def help(self) -> str | None:
        return str(type(self).__doc__)

    @property
    @abc.abstractmethod
    def command_hint(self) -> str | None:
        pass

    @abc.abstractmethod
    def matches(self, message: str) -> bool:
        """Check if this command is matched"""

    @abc.abstractmethod
    async def process(self, context: MessageContext, message: str) -> bool:
        """Handle the command in the message"""


@runtime_checkable
class ReactionHandler(Protocol):
    async def handle_reaction(
        self,
        event: discord.RawReactionActionEvent,
        *,
        removed: bool,
    ) -> None:
        pass


@runtime_checkable
class MemberHandler(Protocol):
    async def handle_member(self, before: discord.Member, after: discord.Member) -> None:
        pass

    def record_activity(self, guild: discord.Guild, member: discord.Member) -> None:
        pass


@runtime_checkable
class ClientHandler(Protocol):
    async def setup(self, client: discord.Client) -> asyncio.Task[None] | None:
        pass


class BlankContextManager(AbstractAsyncContextManager[None]):
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        pass


class SimpleCommand(Command, abc.ABC):
    """A command with no arguments which returns a string."""

    _command: str

    def __init__(self, command: str) -> None:
        self._command = "!" + command.strip().lower()

    @property
    def command_hint(self) -> str:
        return self._command

    def matches(self, message: str) -> bool:
        """Check if this command is matched"""
        return message.lower() == self._command or message.lower().startswith(
            self._command + " ",
        )

    async def process(self, context: MessageContext, _: str) -> bool:
        """Handle the command in the message"""
        reply = await self.message()

        if reply is None:
            return False

        await context.reply_all(reply)

        return True

    @abc.abstractmethod
    async def message(self) -> str | None:
        pass


class RateLimitCommand(Command):
    """Command decorator that rate limits a command"""

    _last: float = 0
    _interval: float
    _command: Command

    def __init__(self, command: Command, interval: float) -> None:
        self._command = command
        self._interval = interval

    @property
    def group(self) -> str | None:
        return self._command.group

    @property
    def help(self) -> str | None:
        return self._command.help

    @property
    def command_hint(self) -> str | None:
        return self._command.command_hint

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

    def __init__(self, command: str, min_args: int, max_args: int) -> None:
        self._command = "!" + command.strip().lower()
        self._min_args = min_args
        self._max_args = max_args

        if self._min_args > 0:
            self._command += " "

    @property
    def command_hint(self) -> str | None:
        if self._min_args == self._max_args:
            return self._command + f"[{self._min_args} args]"
        return self._command + f"[{self._min_args}-{self._max_args} args]"

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
        """Process the command with its arguments"""
