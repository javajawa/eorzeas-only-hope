# SPDX-FileCopyrightText: 2025 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations as _future_annotations

import asyncio
import collections
import datetime
import logging
import sqlite3
import zoneinfo

from discord import (
    Client,
    Guild,
    Member,
    Message,
    RawReactionActionEvent,
    Reaction,
    Role,
    TextChannel,
    User,
)

from bot.commands import Command, MessageContext
from bot.discord import DiscordMessageContext

GuildID = int
ChannelID = int
MessageID = int
RoleID = int


CURSED_CORD: GuildID = 441658759249657859


class AirLock(Command):
    _logger: logging.Logger
    _client: Client
    _db: sqlite3.Connection
    _stop_event: asyncio.Event

    _general_channel: TextChannel | None
    _pending_new_users: set[Member]
    _pending_activity: dict[tuple[GuildID, int], datetime.datetime]
    _announce_task: asyncio.Task[None] | None
    activity_task: asyncio.Task[None] | None

    def __init__(self, logger: logging.Logger, db: sqlite3.Connection) -> None:
        self._logger = logger
        self._db = db
        self._stop_event = asyncio.Event()
        self._general_channel = None
        self._announce_task = None
        self.activity_task = None
        self._pending_new_users = set()
        self._pending_activity = {}

    async def setup(self, client: Client) -> asyncio.Task[None]:
        if not (guild := client.get_guild(CURSED_CORD)):
            raise ValueError

        channel = guild.get_channel(CursedCordChannels.GENERAL)

        if not isinstance(channel, TextChannel):
            raise TypeError

        self._client = client
        self._general_channel = channel
        self.activity_task = client.loop.create_task(self._background_tasks())

        return client.loop.create_task(self.record_users(), name="Record users")

    async def handle_member(self, before: Member, after: Member) -> None:
        # Ignore if the users is already through the AirLock
        if CursedCordRoles.AIRLOCK_SURVIVOR in [r.id for r in before.roles]:
            return

        # Ignore if the users is not yet through the airlock
        # (also remove them from the pending if they are removed)
        if CursedCordRoles.AIRLOCK_SURVIVOR not in [r.id for r in after.roles]:
            self._pending_new_users.discard(after)
            return

        # Add this user to the queue
        self._logger.info("Adding %s to the welcome queue", after.name)
        self._pending_new_users.add(after)

        if not self._announce_task:
            self._announce_task = asyncio.create_task(
                self.send_welcome_message(),
                name="Send welcome message",
            )

    async def send_welcome_message(self) -> None:
        """Sends a welcome message with recently approved users."""
        try:
            self._logger.info("Starting countdown to welcome new users.")
            await asyncio.sleep(90)
        except asyncio.CancelledError:
            pass

        if not self._general_channel or not self._pending_new_users:
            self._logger.error("No new users when the sending the welcome message??")
            return

        mentions = [mem.mention for mem in self._pending_new_users]
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
        self._pending_new_users = set()

    async def record_users(self) -> None:
        cursor = self._db.cursor()

        for guild in self._client.guilds:
            self._logger.info("Recording Member info for %s (%d)", guild.name, guild.id)
            for member in guild.members:
                recorded_roles = [role.name for role in member.roles if role.is_assignable()]

                cursor.execute(
                    """
                    INSERT INTO Users (guild_id, user_id, username, nick, join_date, roles)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT (guild_id, user_id)
                    DO UPDATE SET
                        username = excluded.username,
                        nick = excluded.nick,
                        roles = excluded.roles
                    """,
                    (
                        guild.id,
                        member.id,
                        member.global_name or member.name,
                        member.nick or member.name,
                        int(member.joined_at.timestamp()) if member.joined_at else 0,
                        ", ".join(recorded_roles),
                    ),
                )

        cursor.close()
        self._db.commit()

    def record_activity(self, guild: Guild, member: Member) -> None:
        self._pending_activity[(guild.id, member.id)] = datetime.datetime.now(datetime.UTC)

    @property
    def group(self) -> str:
        return "Discord"

    @property
    def command_hint(self) -> str:
        return "!birthday"

    @property
    def help(self) -> str:
        return (
            "Set your birthday with `!birthday [date] [timezone]` "
            "(e.g. `!birthday 1900-01-30 Europe/London`),"
            "or remove with `!birthday off`"
        )

    def matches(self, message: str) -> bool:
        return message.startswith("!birthday")

    async def process(self, context: MessageContext, message: str) -> bool:
        if not isinstance(context, DiscordMessageContext):
            return False

        user = context.message.author

        args = message.split()[1:]
        return await self._handle_birthday_update(context, user, args)

    async def _handle_birthday_update(
        self,
        context: DiscordMessageContext,
        user: User | Member,
        args: list[str],
    ) -> bool:
        if len(args) > 2:
            await context.reply_direct(
                "Command format: `!birthday [date] [timezone]` "
                "e.g. `!birthday 1900-01-30 Europe/London`",
            )
            return False

        if not args:
            if bday := self.get_user_birthday(user):
                await context.reply_direct(
                    "Current birthday date="
                    + bday.date().isoformat()
                    + ", timezone="
                    + str(bday.tzinfo),
                )
            else:
                await context.reply_direct("Your birthday is not configured.")
            return True

        if args == ["off"]:
            self._db.execute("DELETE FROM UserBirthday WHERE user_id = ?", (user.id,))
            self._db.commit()
            await context.react()
            return True

        if len(args) == 1:
            args.append("Etc/UTC")

        try:
            self._store_birthday(user, *args)
            await context.react()
        except ValueError as exc:
            await context.reply_direct(str(exc))

        return True

    def _store_birthday(self, user: User | Member, date: str, tz: str) -> None:
        try:
            bday = datetime.datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=datetime.UTC)
        except ValueError as exc:
            raise ValueError("Invalid date format") from exc

        try:
            zone = zoneinfo.ZoneInfo(tz)
        except zoneinfo.ZoneInfoNotFoundError as exc:
            raise ValueError(
                "Invalid timezone (common ones are 'America/Toronto', 'America/Vancouver', "
                "'Europe/London', 'Europe/Berlin'...someone a long time ago made a decision "
                "to name them after places but only list some places. It's a right pain. "
                "Anything marked 'Canonical' in "
                "https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List "
                "should work).",
            ) from exc

        next_bday = self.calculate_next_birthday(bday.month, bday.day, zone)

        self._db.execute(
            """INSERT INTO UserBirthday (user_id, bday_year, bday_month, bday_day, timezone, next)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (user_id) DO UPDATE SET
                bday_year = EXCLUDED.bday_year,
                bday_month = EXCLUDED.bday_month,
                bday_day = EXCLUDED.bday_day,
                timezone = EXCLUDED.timezone,
                next = EXCLUDED.next
            """,
            (user.id, bday.year, bday.month, bday.day, tz, next_bday.timestamp()),
        )
        self._db.commit()

    def get_user_birthday(self, user: User | Member) -> datetime.datetime | None:
        for row in self._db.execute(
            "SELECT bday_year, bday_month, bday_day, timezone FROM UserBirthday WHERE user_id = ?",
            (user.id,),
        ):
            return datetime.datetime.now(tz=zoneinfo.ZoneInfo(row[3])).replace(
                year=row[0],
                month=row[1],
                day=row[2],
            )

        return None

    def calculate_next_birthday(
        self,
        bday_month: int,
        bday_day: int,
        tz: zoneinfo.ZoneInfo,
    ) -> datetime.datetime:
        now = datetime.datetime.now(tz=tz)
        next_bday = now.replace(
            month=bday_month,
            day=bday_day,
            hour=11,
            minute=0,
            second=0,
            microsecond=0,
        )

        if next_bday < now:
            next_bday = next_bday.replace(year=next_bday.year + 1)

        return next_bday

    async def _background_tasks(self) -> None:
        while not self._stop_event.is_set():
            try:
                await asyncio.sleep(300)
            except asyncio.CancelledError:
                self._stop_event.set()

            cursor = self._db.cursor()
            try:
                await self._flush_member_activity(cursor)
                await self._process_birthdays(cursor)
            except Exception as exc:
                self._logger.exception("Background task error", exc_info=exc)
            cursor.close()
            self._db.commit()

    async def _flush_member_activity(self, cursor: sqlite3.Cursor) -> None:
        for (guild, member), timestamp in self._pending_activity.items():
            cursor.execute(
                """UPDATE Users SET last_activity = ? WHERE guild_id = ? AND user_id = ?""",
                (int(timestamp.timestamp()), guild, member),
            )

        self._logger.debug("Updated activity for %d members", len(self._pending_activity))
        self._pending_activity.clear()

    async def _process_birthdays(self, cursor: sqlite3.Cursor) -> None:
        if not self._client:
            return

        cursor.execute(
            """SELECT user_id, bday_month, bday_day, timezone
            FROM UserBirthday NATURAL JOIN Users
            WHERE guild_id = ? AND next < unixepoch() AND last_activity > unixepoch() - 10000000""",
            (CURSED_CORD,),
        )
        rows = cursor.fetchall()

        if not rows:
            return

        if not (cursedcord := self._client.get_guild(CURSED_CORD)):
            return

        channel = cursedcord.get_channel(CursedCordChannels.GENERAL)
        if not isinstance(channel, TextChannel):
            return

        for user_id, bday_month, bday_day, tz in rows:
            if not (member := cursedcord.get_member(user_id)):
                continue

            await channel.send(
                "Happy Birthday " + member.mention + "!\n-# CAKE! CAKE! CAKE! CAKE! CAKE!",
            )
            next_bday = self.calculate_next_birthday(bday_month, bday_day, zoneinfo.ZoneInfo(tz))
            cursor.execute(
                "UPDATE UserBirthday SET next = ? WHERE user_id = ?",
                (next_bday.timestamp(), user_id),
            )


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


class RoleReactionHandler(Command):
    _logger: logging.Logger
    _client: Client | None

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger
        self._client = None

    async def setup(self, client: Client) -> asyncio.Task[None]:
        self._client = client
        return client.loop.create_task(self.resync_roles(), name="resync-discord-roles")

    async def handle_reaction(self, event: RawReactionActionEvent, *, removed: bool) -> None:
        role_id = (
            ROLE_REACTION_CONFIGURATION.get(event.guild_id or 0, {})
            .get(event.channel_id, {})
            .get(event.message_id, {})
            .get(event.emoji.name)
        )

        if not self._client or not role_id:
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

        if not self._client:
            return

        for guild_id in ROLE_REACTION_CONFIGURATION:
            guild = self._client.get_guild(guild_id)

            if not guild:
                continue

            roles, members = await self.get_desired_member_roles(guild)
            await self.sync_roles(roles, members)

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

    @property
    def command_hint(self) -> str | None:
        return None

    def matches(self, _: str) -> bool:
        return False

    async def process(self, _: MessageContext, __: str) -> bool:
        return False
