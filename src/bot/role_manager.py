# SPDX-FileCopyrightText: 2025 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations as _future_annotations

import asyncio
import csv
import logging
import pathlib

from discord import (
    Client,
    Guild,
    Member,
    Message,
    RawReactionActionEvent,
    Reaction,
    Role,
    TextChannel,
)

GuildID = int
ChannelID = int
MessageID = int
RoleID = int

role_map: dict[GuildID, dict[ChannelID, dict[MessageID, dict[str, RoleID]]]] = {
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
                "🎤": 1055912632231673998,
                "💠": 1156426270511464478,
                "🏒": 1363638377873670385,
            },
        },
    },
}


def reaction_to_role(reaction: RawReactionActionEvent) -> RoleID | None:
    return (
        role_map.get(reaction.guild_id or 0, {})
        .get(reaction.channel_id, {})
        .get(reaction.message_id, {})
        .get(reaction.emoji.name)
    )


async def resync_roles(client: Client) -> None:
    for guild_id in role_map:
        guild = client.get_guild(guild_id)

        if not guild:
            continue

        roles, members = await get_member_roles(guild)
        await sync_roles(roles, members)
        record_users(list(members))


def record_users(members: list[Member]) -> None:
    with pathlib.Path("users.csv").open("w", encoding="utf-8") as f:
        data = csv.DictWriter(f, ("User ID", "Username", "Nickname", "Joined At", "Roles"))

        for member in members:
            data.writerow(
                {
                    "User ID": member.id,
                    "Username": member.name,
                    "Nickname": member.nick or member.global_name,
                    "Joined At": member.joined_at,
                    "Roles": [role.name for role in member.roles if role.is_assignable()],
                },
            )


async def get_member_roles(guild: Guild) -> tuple[set[Role], dict[Member, set[Role]]]:
    managed_roles: set[Role] = set()
    members: dict[Member, set[Role]] = {m: set() for m in guild.members}

    for channel_id, messages in role_map.get(guild.id, {}).items():
        channel = guild.get_channel(channel_id)

        if not isinstance(channel, TextChannel):
            continue

        for message_id, emotes in messages.items():
            message = await channel.fetch_message(message_id)
            if not message:
                continue

            managed_roles.union(await role_maps_for_message(guild, message, members, emotes))

    # Bots don't get these managed roles
    for member in list(members):
        if member.bot:
            members[member] = set()

    return managed_roles, members


async def role_maps_for_message(
    guild: Guild,
    message: Message,
    members: dict[Member, set[Role]],
    emotes: dict[str, RoleID],
) -> set[Role]:
    roles: set[Role] = set()

    reactions: dict[str, Reaction] = {str(r.emoji): r for r in message.reactions}

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


async def sync_roles(roles: set[Role], members: dict[Member, set[Role]]) -> None:
    logger = logging.getLogger("role-sync")

    for member, roles_requested in members.items():
        member_roles = set(member.roles)
        roles_unrequested = roles - roles_requested
        roles_to_add = roles_requested - member_roles
        roles_to_remove = roles_unrequested.intersection(member_roles)

        if roles_to_add:
            logger.info(
                "Adding roles %s to %s",
                [role.name for role in roles_to_add],
                member,
            )
            await member.add_roles(*roles_to_add)

        if roles_to_remove:
            logger.info(
                "Removing roles %s from %s",
                [role.name for role in roles_to_remove],
                member,
            )
            await member.remove_roles(*roles_to_remove)


class AirLock:
    _logger: logging.Logger
    _airlock_role: Role
    _general_channel: TextChannel
    _new_users: set[Member]
    _announce_task: asyncio.Task[None] | None

    def __init__(self, logger: logging.Logger, client: Client) -> None:
        self._logger = logger

        guild = client.get_guild(441658759249657859)

        if not guild:
            raise ValueError

        role = guild.get_role(1438871865044238448)
        channel = guild.get_channel(441658759249657861)

        if not role or not channel or not isinstance(channel, TextChannel):
            raise ValueError

        self._airlock_role = role
        self._general_channel = channel
        self._new_users = set()
        self._announce_task = None

    async def send_welcome_message(self) -> None:
        try:
            self._logger.info("Starting countdown to welcome new users.")
            await asyncio.sleep(90)
        except asyncio.CancelledError:
            pass

        if not self._new_users:
            self._logger.error("No new users when the sending the welcome message??")
            return

        mentions = [mem.mention for mem in self._new_users]
        self._logger.info("Sending welcome message for %s", mentions)

        if len(mentions) == 1:
            mention_str = mentions[0]
        elif len(mentions) == 2:
            mention_str = " and ".join(mentions)
        else:
            mention_str = ", ".join(mentions[:-1]) + ", and " + mentions[-1]

        message = "Hello and welcome to " + mention_str + "!"
        message += "\n-# Please find server rules and welcome guide in the pins of this channel."
        await self._general_channel.send(message)
        self._announce_task = None
        self._new_users = set()

    async def on_member_change(self, before: Member, after: Member) -> None:
        # Ignore if the users is already through the AirLock
        if self._airlock_role in before.roles:
            return

        # Ignore if the users is not yet through the airlock
        if self._airlock_role not in after.roles:
            return

        # Add this user to the queue
        self._logger.info("Adding %s to the welcome queue", after.name)
        self._new_users.add(after)

        if not self._announce_task:
            self._announce_task = asyncio.create_task(
                self.send_welcome_message(),
                name="Send welcome message",
            )
