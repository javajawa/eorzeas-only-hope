# SPDX-FileCopyrightText: 2025 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations as _future_annotations

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
