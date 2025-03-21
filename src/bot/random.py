# SPDX-FileCopyrightText: 2025 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations as _future_annotations

from typing import NotRequired, TypedDict

import io
import random
import re

import discord

from bot.commands import Command, MessageContext
from bot.twitch import TwitchMessageContext


class Config(TypedDict):
    group: NotRequired[str]
    help: NotRequired[str]
    channels: NotRequired[list[str]]
    commands: NotRequired[list[str]]
    regexp: NotRequired[str]
    formats: list[str]
    args: NotRequired[dict[str, list[str]]]


class RandomCommand(Command):
    _group: str
    _doc: str
    _channels: set[str]
    _commands: list[str]
    _regexp: re.Pattern[str] | None
    _formats: list[str]
    _args: dict[str, list[str]]

    def __init__(self, config: Config) -> None:
        commands = config.get("commands", [])

        self._group = config.get("group", "")
        self._doc = config.get("help", "")
        self._channels = set(config.get("channels", []))
        self._commands = ["!" + trigger.strip("!") for trigger in commands]
        self._regexp = re.compile(config["regexp"], re.IGNORECASE) if "regexp" in config else None
        self._formats = list(map(str, config.get("formats", [])))
        self._args = {k: [str(x) for x in v] for k, v in config.get("args", {}).items()}

    @property
    def command_hint(self) -> str | None:
        if self._channels and "discord" not in self._channels:
            return None
        if not self._doc and not self._group:
            return None

        return "/".join(self._commands)

    @property
    def group(self) -> str | None:
        return self._group if self._group else None

    @property
    def help(self) -> str:
        return self._doc

    def matches(self, message: str) -> bool:
        if self._regexp and self._regexp.search(message) is not None:
            return True

        return any(
            any(line.startswith(x + " ") or line == x for x in self._commands)
            for line in message.split("\n")
        )

    def in_channel(self, context: MessageContext | None) -> bool:
        if not self._channels:
            return True

        if isinstance(context, TwitchMessageContext):
            return str(context.channel()) in self._channels

        return "discord" in self._channels

    async def process(self, context: MessageContext, _: str) -> bool:
        if not self.in_channel(context):
            return False

        reply_format = random.choice(self._formats)

        if not reply_format:
            return False

        args = {k: random.choice(self._args[k]) for k in self._args}
        args["sender"] = context.sender()

        reply = reply_format.format(**args)

        await context.reply_all(reply)
        return True


class HelpCommand(Command):
    _blocks: list[str]

    def __init__(self, commands: list[Command]) -> None:
        help_lines: dict[str | None, list[str]] = {}
        blocks: list[str] = []

        for command in commands:
            if not command.command_hint:
                continue
            group = help_lines.setdefault(command.group, [])
            if command.help:
                group.append(f"`{command.command_hint}` - {command.help}")
            else:
                group.append(f"`{command.command_hint}`")

        cur_block = io.StringIO()
        cur_block.write("## HopeBot Commands\n")

        for command_group, group in help_lines.items():
            cur_block.write(f"### {command_group}\n")
            for command_help in group:
                if cur_block.tell() + len(command_help) >= 2000:
                    blocks.append(cur_block.getvalue())
                    cur_block = io.StringIO()

                cur_block.write("- ")
                cur_block.write(command_help)
                cur_block.write("\n")

        blocks.append(cur_block.getvalue())
        self._blocks = blocks

    @property
    def command_hint(self) -> str | None:
        return None

    @property
    def group(self) -> str | None:
        return None

    def matches(self, message: str) -> bool:
        return message == "!help"

    async def process(self, context: MessageContext, _: str) -> bool:
        try:
            for block in self._blocks:
                await context.reply_direct(block)
        except discord.errors.Forbidden:
            await context.reply_all(f"Oi, {context.sender()}, your DMs aren't open.")

        return True
