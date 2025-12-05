# SPDX-FileCopyrightText: 2025 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations as _future_annotations

import asyncio
import collections
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


CURSED_CORD: GuildID = 441658759249657859


class CursedCordChannels:
    GENERAL: ChannelID = 441658759249657861
    ROLE_SET: ChannelID = 672539104118046760


class CursedCordRoles:
    AIRLOCK_SURVIVOR: RoleID = 1438871865044238448

    PRONOUN_THEY_THEM: RoleID = 666106737488822282
    PRONOUN_SHE_HER: RoleID = 666107349714337812
    PRONOUN_HE_HIM: RoleID = 666107206621462528
    PRONOUN_HE_THEY: RoleID = 793580028822421564
    PRONOUN_SHE_THEY: RoleID = 793580189069344768

    KITT: RoleID = 793485330904252426
    SOCIAL_CHATTERER: RoleID = 1055912632231673998
    POE_HIDEOUT_WANTER: RoleID = 1156426270511464478
    SPLORTS_FAN: RoleID = 1363638377873670385
    BOARDGAMER: RoleID = 784575348352352258
    MAHJONG: RoleID = 863160693960474624


ROLE_REACTION_CONFIGURATION: dict[GuildID, dict[ChannelID, dict[MessageID, dict[str, RoleID]]]] = {
    CURSED_CORD: {
        CursedCordChannels.ROLE_SET: {
            672542715996536865: {
                "👻": CursedCordRoles.PRONOUN_THEY_THEM,
                "💀": CursedCordRoles.PRONOUN_SHE_HER,
                "☠️": CursedCordRoles.PRONOUN_HE_HIM,
                "⚪": CursedCordRoles.PRONOUN_HE_THEY,
                "⬜": CursedCordRoles.PRONOUN_SHE_THEY,
            },
            784575768234819584: {
                "♟️": CursedCordRoles.BOARDGAMER,
                "🐱": CursedCordRoles.KITT,
                "🀄": CursedCordRoles.MAHJONG,
                "🎤": CursedCordRoles.SOCIAL_CHATTERER,
                "💠": CursedCordRoles.POE_HIDEOUT_WANTER,
                "🏒": CursedCordRoles.SPLORTS_FAN,
            },
        },
    },
}


class RoleReactionHandler:
    _logger: logging.Logger
    _client: Client

    def __init__(self, logger: logging.Logger, client: Client) -> None:
        self._logger = logger
        self._client = client

    async def handle_reaction(self, event: RawReactionActionEvent, *, removed: bool) -> None:
        role_id = (
            ROLE_REACTION_CONFIGURATION.get(event.guild_id or 0, {})
            .get(event.channel_id, {})
            .get(event.message_id, {})
            .get(event.emoji.name)
        )

        if not role_id:
            return

        guild = self._client.get_guild(event.guild_id or 0)

        if not guild:
            return

        member = guild.get_member(event.user_id)
        role = guild.get_role(role_id)

        if not member or not role:
            return

        if removed and role in member.roles:
            self._logger.info("Removing role %s from %s", role, member.name)
            await member.remove_roles(role)
        elif not removed and role not in member.roles:
            self._logger.info("Adding role %s to %s", role, member.name)
            await member.add_roles(role)

    async def resync_roles(self) -> None:
        """Resynchronise all reaction roles across guilds."""

        for guild_id in ROLE_REACTION_CONFIGURATION:
            guild = self._client.get_guild(guild_id)

            if not guild:
                continue

            roles, members = await self.get_desired_member_roles(guild)
            await self.sync_roles(roles, members)
            record_users(list(members))

    async def get_desired_member_roles(
        self,
        guild: Guild,
    ) -> tuple[set[Role], dict[Member, set[Role]]]:
        managed_roles: set[Role] = set()
        members: dict[Member, set[Role]] = {m: set() for m in guild.members if not m.bot}

        for channel_id, messages in ROLE_REACTION_CONFIGURATION.get(guild.id, {}).items():
            channel = guild.get_channel(channel_id)

            if not isinstance(channel, TextChannel):
                continue

            for message_id, emotes in messages.items():
                message = await channel.fetch_message(message_id)
                if not message:
                    continue

                message_roles = await self._prepare_message(guild, message, emotes)
                managed_roles.update(message_roles.values())

                current_reactions = await self._get_current_reactions(message, message_roles)
                for member, roles in current_reactions.items():
                    if member in members:  # Leavers can leave reactions around.
                        members[member].update(roles)

        return managed_roles, members

    async def _prepare_message(
        self,
        guild: Guild,
        message: Message,
        emotes: dict[str, RoleID],
    ) -> dict[str, Role]:
        """Ensure that all valid emoji are present on a message, and return the mapped roles."""
        roles: dict[str, Role] = {}
        reactions: dict[str, bool] = {str(r.emoji): r.me for r in message.reactions}

        for emote, role_id in emotes.items():
            if role := guild.get_role(role_id):
                roles[emote] = role

                # Ensure that the bot has made the reaction (so the emote always exists).
                if emote not in reactions or not reactions[emote]:
                    await message.add_reaction(emote)

        return roles

    async def _get_current_reactions(
        self,
        message: Message,
        message_roles: dict[str, Role],
    ) -> dict[Member, set[Role]]:
        reactions: dict[str, Reaction] = {str(r.emoji): r for r in message.reactions}
        result: dict[Member, set[Role]] = collections.defaultdict(set)

        for emote, role in message_roles.items():
            async for member in reactions[emote].users():
                if isinstance(member, Member):
                    result[member].add(role)

        return result

    async def sync_roles(self, roles: set[Role], members: dict[Member, set[Role]]) -> None:
        for member, roles_requested in members.items():
            member_roles = set(member.roles)
            roles_unrequested = roles - roles_requested
            roles_to_add = roles_requested - member_roles
            roles_to_remove = roles_unrequested.intersection(member_roles)

            if roles_to_add:
                self._logger.info(
                    "Adding roles %s to %s",
                    [role.name for role in roles_to_add],
                    member,
                )
                await member.add_roles(*roles_to_add)

            if roles_to_remove:
                self._logger.info(
                    "Removing roles %s from %s",
                    [role.name for role in roles_to_remove],
                    member,
                )
                await member.remove_roles(*roles_to_remove)


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


class AirLock:
    _logger: logging.Logger
    _airlock_role: Role
    _general_channel: TextChannel
    _new_users: set[Member]
    _announce_task: asyncio.Task[None] | None

    def __init__(self, logger: logging.Logger, client: Client) -> None:
        self._logger = logger

        if not (guild := client.get_guild(CURSED_CORD)):
            raise ValueError

        role = guild.get_role(CursedCordRoles.AIRLOCK_SURVIVOR)
        channel = guild.get_channel(CursedCordChannels.GENERAL)

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
