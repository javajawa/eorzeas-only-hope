#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""The Discord bot"""

from __future__ import annotations

from typing import Dict, List, Union, Optional, Set, Tuple

import asyncio
import time

# noinspection PyPackageRequirements
from discord import (
    Client,
    Embed,
    Member,
    Message,
    Intents,
    DMChannel,
    Guild,
    RawReactionActionEvent,
    Reaction,
    Role,
    TextChannel,
    User,
    VoiceChannel,
    VoiceState,
)

from bot.basebot import BaseBot
from bot.commands import Command, MessageContext


VOICE_RELEVANT_CHANNEL = 779101163387486244
GENERAL_VOICE_CHANNEL = 441658759249657863


GuildID = int
ChannelID = int
MessageID = int
RoleID = int

role_map: Dict[GuildID, Dict[ChannelID, Dict[MessageID, Dict[str, RoleID]]]] = {
    441658759249657859: {
        672539104118046760: {
            672542715996536865: {
                "👻": 666106737488822282,
                "💀": 666107349714337812,
                "☠️": 666107206621462528,
                "⚪": 793580028822421564,
                "⬜": 793580189069344768,
            },
            784575768234819584: {
                "♟️": 784575348352352258,
                "🐱": 793485330904252426,
                "🀄": 863160693960474624,
            },
        }
    }
}


class DiscordBot(Client, BaseBot):
    """The Discord bot"""

    _changes: Dict[int, Tuple[str, float, float]]

    def __init__(self: DiscordBot, loop: asyncio.AbstractEventLoop, commands: List[Command]):
        intents = Intents.all()

        BaseBot.__init__(self, commands)
        Client.__init__(self, intents=intents, loop=loop)

        self._changes = {}

    async def on_ready(self: DiscordBot) -> None:
        """When the bot connects."""
        print(f"{self.user} has connected to Discord!")
        self.loop.create_task(self.resync_roles())

    async def on_message(self: DiscordBot, message: Message) -> None:
        """When a message is received."""
        if message.author == self.user:
            return

        if message.guild and message.channel.id == VOICE_RELEVANT_CHANNEL:
            if message.content.startswith("!activity"):
                channel = message.guild.get_channel(GENERAL_VOICE_CHANNEL)

                if isinstance(channel, VoiceChannel):
                    name = message.content.replace("!activity", "").strip()
                    name = "General - " + name if channel.members and name else "General"

                    self.loop.create_task(
                        self.request_name_change(
                            channel, name, "Requested by " + str(message.author)
                        )
                    )

        await self.process(DiscordMessageContext(message), message.content)

    async def resync_roles(self) -> None:
        for guild_id in role_map:
            guild = self.get_guild(guild_id)

            if not guild:
                continue

            roles, members = await self.get_member_roles(guild)
            await self.sync_roles(roles, members)

    @staticmethod
    async def get_member_roles(guild: Guild) -> Tuple[Set[Role], Dict[Member, Set[Role]]]:
        managed_roles: Set[Role] = set()
        members: Dict[Member, Set[Role]] = {m: set() for m in guild.members}

        for channel_id, messages in role_map.get(guild.id, {}).items():
            channel = guild.get_channel(channel_id)

            if not isinstance(channel, TextChannel):
                continue

            for message_id, emotes in messages.items():
                message = await channel.fetch_message(message_id)
                if not message:
                    continue

                managed_roles.union(
                    await DiscordBot.role_maps_for_message(guild, message, members, emotes)
                )

        return managed_roles, members

    @staticmethod
    async def role_maps_for_message(
        guild: Guild,
        message: Message,
        members: Dict[Member, Set[Role]],
        emotes: Dict[str, RoleID],
    ) -> Set[Role]:
        roles: Set[Role] = set()

        reactions: Dict[str, Reaction] = {str(r.emoji): r for r in message.reactions}

        for emote, role_id in emotes.items():
            role = guild.get_role(role_id)

            if not role:
                continue

            roles.add(role)

            # Ensure that the emote exists at all.
            if emote not in reactions or not reactions[emote].me:
                await message.add_reaction(emote)

            async for user in reactions[emote].users():
                # Ignore reactions from people who have left the server
                if isinstance(user, Member) and user in members:
                    members[user].add(role)

        return roles

    @staticmethod
    async def sync_roles(roles: Set[Role], members: Dict[Member, Set[Role]]) -> None:
        for member, roles_requested in members.items():
            # Bots don't get these managed roles
            if member.bot:
                roles_requested = set()

            member_roles = set(member.roles)
            roles_unrequested = roles - roles_requested
            roles_to_add = roles_requested - member_roles
            roles_to_remove = roles_unrequested.intersection(member_roles)

            if roles_to_add:
                print("Adding roles", [role.name for role in roles_to_add], "to", member)
                await member.add_roles(*roles_to_add)

            if roles_to_remove:
                print(
                    "Removing roles",
                    [role.name for role in roles_to_remove],
                    "from",
                    member,
                )
                await member.remove_roles(*roles_to_remove)

    async def on_raw_reaction_add(self, reaction: RawReactionActionEvent) -> None:
        """Handle random reactions"""
        role_id = self.reaction_to_role(reaction)

        if not role_id:
            return

        guild = self.get_guild(reaction.guild_id or 0)

        if not guild:
            return

        member = guild.get_member(reaction.user_id)
        role = guild.get_role(role_id)

        if role and member and not member.get_role(role_id):
            print("Adding", role, "to", member)
            await member.add_roles(role)

    async def on_raw_reaction_remove(self, reaction: RawReactionActionEvent) -> None:
        """Handle random reactions"""
        role_id = self.reaction_to_role(reaction)

        if not role_id:
            return

        guild = self.get_guild(reaction.guild_id or 0)

        if not guild:
            return

        member = guild.get_member(reaction.user_id)
        role = guild.get_role(role_id)

        if role and member and member.get_role(role_id):
            print("Remove", role, "to", member)
            await member.remove_roles(role)

    def reaction_to_role(self, reaction: RawReactionActionEvent) -> Optional[RoleID]:
        if not self.user or reaction.user_id == self.user.id:
            return None

        return (
            role_map.get(reaction.guild_id or 0, {})
            .get(reaction.channel_id, {})
            .get(reaction.message_id, {})
            .get(reaction.emoji.name)
        )

    # noinspection PyUnusedLocal
    # pylint: disable=unused-argument
    async def on_reaction_add(self, reaction: Reaction, user: User) -> None:
        if reaction.message.author != self.user:
            return

        if reaction.emoji == "❌":
            await reaction.message.edit(content="[Bot message removed by user request]")
        if (reaction.emoji == "❗") and ("||" not in reaction.message.content):
            await reaction.message.edit(
                content="||" + reaction.message.content + "||", suppress=True
            )

    async def on_voice_state_update(
        self, member: Member, before: VoiceState, after: VoiceState
    ) -> None:
        # We only care about people leaving the general voice channel
        if not before.channel or before.channel.id != GENERAL_VOICE_CHANNEL:
            return

        # If they're still there, we no care.
        if after.channel and after.channel.id == GENERAL_VOICE_CHANNEL:
            return

        if not before.channel.members:
            self.loop.create_task(
                self.request_name_change(
                    before.channel, "General", "No users left in channel"  # type: ignore
                )
            )

    async def request_name_change(
        self, channel: VoiceChannel, name: str, reason: str
    ) -> None:
        if name == channel.name:
            return

        target, time1, time2 = self._changes.get(channel.id, ("", 0, 0))

        if target == name:
            return

        self._changes[channel.id] = (name, time1, time2)

        wait = time2 - time.time() + 610

        if wait > 10:
            feedback = channel.guild.get_channel(VOICE_RELEVANT_CHANNEL)
            if isinstance(feedback, TextChannel):
                await feedback.send(
                    content=(
                        f"Rate limited, channel name will update "
                        f"to '{name}; later ({int(wait)}s)"
                    )
                )
            await asyncio.sleep(wait)

        if self._changes[channel.id][0] != name:
            return

        self._changes[channel.id] = (name, time.time(), time1)
        await channel.edit(name=name, reason=reason)


class DiscordMessageContext(MessageContext):
    """Discord message context."""

    _message: Message

    def __init__(self, message: Message):
        self._message = message

    async def reply_direct(self, message: str) -> None:
        """Reply directly to the user who sent this message."""
        await self._message.author.send(message)

    async def reply_all(self, message: Union[str, Embed]) -> None:
        """Reply to the channel this message was received in"""

        if isinstance(message, Embed):
            await self._message.channel.send(embed=message)
        else:
            await self._message.channel.send(message)

    async def react(self) -> None:
        """React to the message, indicating successful processing."""
        await self._message.add_reaction("\U0001F44D")

    def sender(self) -> str:
        return str(self._message.author.name) + "#" + str(self._message.author.discriminator)

    def channel(self) -> str:
        if isinstance(self._message.channel, DMChannel):
            return "[DMs]"

        return str(self._message.channel.name)  # type: ignore
