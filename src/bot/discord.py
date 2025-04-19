# SPDX-FileCopyrightText: 2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""The Discord bot"""

from __future__ import annotations as _future_annotations

import asyncio
import logging
from contextlib import AbstractAsyncContextManager

import discord

# noinspection PyPackageRequirements
from discord import (
    Client,
    DMChannel,
    Embed,
    Intents,
    Member,
    Message,
    PartialMessageable,
    RawReactionActionEvent,
    Reaction,
    Role,
    User,
    VoiceState,
    app_commands,
)

import bot.role_manager
import bot.voice_activity
from bot.basebot import BaseBot
from bot.commands import Command, MessageContext, ReactionHandler
from bot.random import HelpCommand


class DiscordBot(Client, BaseBot):
    """The Discord bot"""

    _bot_tasks: set[asyncio.Task[None]]
    _reaction_handlers: set[ReactionHandler]
    _command_tree: app_commands.CommandTree

    def __init__(
        self: DiscordBot,
        logger: logging.Logger,
        loop: asyncio.AbstractEventLoop,
        commands: list[Command],
    ) -> None:
        intents = Intents.all()

        commands.append(HelpCommand(commands))

        BaseBot.__init__(self, logger, commands)
        Client.__init__(self, intents=intents, loop=loop)

        self._bot_tasks = set()
        self._reaction_handlers = {
            command for command in commands if isinstance(command, ReactionHandler)
        }

    def _task_exit(self, task: asyncio.Task[None]) -> None:
        self._bot_tasks.discard(task)

        if exception := task.exception():
            self._logger.exception("Error in discord task", exc_info=exception)

    async def on_ready(self: DiscordBot) -> None:
        """When the bot connects."""
        if not self.user:
            raise RuntimeError

        self._logger.info("%s has connected to Discord!", self.user.name)

        self._logger.info("Starting role sync")
        task = self.loop.create_task(bot.role_manager.resync_roles(self))
        self._bot_tasks.add(task)
        task.add_done_callback(self._task_exit)

        self._logger.info("Starting command sync: %s", self._command_tree.get_commands())
        self._logger.info("Syncing commands: %s", await self._command_tree.sync())

    async def on_message(self: DiscordBot, message: Message) -> None:
        """When a message is received."""
        if message.author == self.user:
            return

        await bot.voice_activity.voice_message(message)
        task = self.loop.create_task(
            self.process(DiscordMessageContext(message), message.content),
        )
        self._bot_tasks.add(task)
        task.add_done_callback(self._task_exit)

    def get_member_and_role(
        self,
        reaction: RawReactionActionEvent,
    ) -> tuple[Member | None, Role | None]:
        role_id = bot.role_manager.reaction_to_role(reaction)

        if not role_id:
            return None, None

        guild = self.get_guild(reaction.guild_id or 0)

        if not guild:
            return None, None

        member = guild.get_member(reaction.user_id)
        role = guild.get_role(role_id)

        return member, role

    async def on_raw_reaction_add(self, reaction: RawReactionActionEvent) -> None:
        """Handle random reactions"""
        if not self.user or reaction.user_id == self.user.id:
            return

        for handler in self._reaction_handlers:
            task = self.loop.create_task(handler.handle_reaction(reaction))
            self._bot_tasks.add(task)
            task.add_done_callback(self._task_exit)

        member, role = self.get_member_and_role(reaction)

        if role and member and not member.get_role(role.id):
            self._logger.info("Adding role %s to %s", role, member)
            await member.add_roles(role)

    async def on_raw_reaction_remove(self, reaction: RawReactionActionEvent) -> None:
        """Handle random reactions"""
        if not self.user or reaction.user_id == self.user.id:
            return

        for handler in self._reaction_handlers:
            task = self.loop.create_task(handler.handle_reaction(reaction))
            self._bot_tasks.add(task)
            task.add_done_callback(self._task_exit)

        member, role = self.get_member_and_role(reaction)

        if role and member and member.get_role(role.id):
            self._logger.info("Remove role %s from %s", role, member)
            await member.remove_roles(role)

    # noinspection PyUnusedLocal
    # pylint: disable=unused-argument
    async def on_reaction_add(self, reaction: Reaction, _: User) -> None:
        if reaction.message.author != self.user:
            return

        if reaction.emoji == "❌":
            await reaction.message.edit(content="[Bot message removed by user request]")
        if (reaction.emoji == "❗") and ("||" not in reaction.message.content):
            await reaction.message.edit(
                content="|| " + reaction.message.content + " ||",
                suppress=False,
            )

    async def on_voice_state_update(
        self,
        _: Member,
        before: VoiceState,
        after: VoiceState,
    ) -> None:
        await bot.voice_activity.voice_state_event(before, after)


class DiscordMessageContext(MessageContext):
    """Discord message context."""

    _message: Message

    def __init__(self, message: Message) -> None:
        self._message = message
        self._channel = message.channel

    async def reply_direct(self, message: str) -> Message:
        """Reply directly to the user who sent this message."""
        return await self._message.author.send(message)

    async def reply_all(self, message: str | Embed) -> Message:
        """Reply to the channel this message was received in"""

        if isinstance(message, Embed):
            return await self._channel.send(embed=message)

        return await self._channel.send(message)

    async def react(self) -> None:
        """React to the message, indicating successful processing."""
        await self._message.add_reaction("\U0001f44d")

    def typing(self) -> AbstractAsyncContextManager[None]:
        return self._message.channel.typing()

    def sender(self) -> str:
        return self._message.author.mention

    def channel(self) -> str:
        if isinstance(self._message.channel, DMChannel):
            return "[DMs]"

        if isinstance(self._message.channel, PartialMessageable):
            return "[Unknown]"

        return str(self._message.channel.name)

    @property
    def message(self) -> discord.Message:
        return self._message
