# SPDX-FileCopyrightText: 2025 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations as _future_annotations

from collections.abc import Awaitable, Callable

import dataclasses
import logging
import pathlib
import random
import re
import urllib.parse
from collections import defaultdict  # pylint: disable=ungrouped-imports

import aiohttp
import discord

from bot.commands import Command, MessageContext
from bot.discord import DiscordMessageContext

MATCH = re.compile("^https://en\\.(?:m\\.)?wikipedia\\.org/wiki/(.+)$")

PLAY_INFO = (
    "Starting a new game of 'Most of These People are Lying'. "
    "Press ➕ to join as a potential bluffer, and ▶️ to pick random an article!"
)

EMOTES = [
    "\u0031\ufe0f\u20e3",
    "\u0032\ufe0f\u20e3",
    "\u0033\ufe0f\u20e3",
    "\u0034\ufe0f\u20e3",
    "\u0035\ufe0f\u20e3",
    "\u0036\ufe0f\u20e3",
    "\u0037\ufe0f\u20e3",
    "\u0038\ufe0f\u20e3",
    "\u0039\ufe0f\u20e3",
]

HELP_TEXT = (pathlib.Path(__file__).parent / "techdif_help.txt").read_text()


@dataclasses.dataclass
class Article:
    link: str
    hint: str

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return self.link == other
        if isinstance(other, Article):
            return self.link == other.link
        return NotImplemented


@dataclasses.dataclass
class Game:
    channel: discord.TextChannel | discord.Thread
    join_message: discord.Message
    players: set[discord.Member]
    play_message: discord.Message | None = None
    active_players: list[discord.Member] | None = None
    correct_player: discord.Member | None = None
    article: Article | None = None


class PeopleAreLying(Command):
    """Tools for playing 'Two of These People Are Lying' in Discord. Use !lie for more details."""

    _logger: logging.Logger
    _session: aiohttp.ClientSession
    _articles: dict[int, list[Article]]
    _games: list[Game]
    _watched_message_ids: set[int]

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._logger = logging.getLogger("people-are-lying")
        self._session = session
        self._articles = defaultdict(list)
        self._games = []
        self._watched_message_ids = set()

    @property
    def command_hint(self) -> str | None:
        return "!lie {add,remove,list,play}"

    @property
    def group(self) -> str | None:
        return "Interactive"

    def matches(self, message: str) -> bool:
        return message == "!lie" or message.startswith("!lie ")

    async def process(self, context: MessageContext, message: str) -> bool:
        """Handle the command in the message"""

        if not isinstance(context, DiscordMessageContext):
            return False

        if message == "!lie":
            await context.reply_direct(HELP_TEXT)
            return True

        command, _, data = message.removeprefix("!lie ").partition(" ")

        options: dict[str, Callable[[DiscordMessageContext, str], Awaitable[bool]]] = {
            "add": self._add_command,
            "remove": self._remove_command,
            "list": self._list_command,
            "play": self._play_command,
        }

        if command not in options:
            return False

        return await options[command](context, data)

    async def _is_dm(self, context: DiscordMessageContext) -> bool:
        if isinstance(context.message.channel, discord.DMChannel):
            return True

        try:
            await context.reply_all("Please send this command via DMs.")
            await context.reply_direct("Please resend your command here!")
        except discord.errors.Forbidden:
            await context.reply_all(f"Oi, {context.sender()}, your DMs aren't open.")

        return False

    async def _add_command(self, context: DiscordMessageContext, data: str) -> bool:
        if not await self._is_dm(context):
            return True

        data = data.strip()
        matched = MATCH.match(data)
        if not matched:
            await context.reply_direct(
                "Please send a full English Wikipedia link, "
                "e.g. https://en.wikipedia.org/wiki/VT_Group",
            )
            return True

        title = urllib.parse.unquote(matched.group(1)).replace("_", " ")
        title, _, _ = title.partition("(")

        article = Article(data, title)
        self._articles[context.message.author.id].append(article)
        await context.react()
        self._logger.info("Add article %s for %s", data, context.message.author)

        for game in self._games:
            if game.play_message:
                continue
            await self._update_join_message(game)

        return True

    async def _remove_command(self, context: DiscordMessageContext, data: str) -> bool:
        if not await self._is_dm(context):
            return True

        self._articles[context.message.author.id].remove(Article(data, data))
        await context.react()
        self._logger.info("Remove article %s for %s", data, context.message.author)

        for game in self._games:
            if game.play_message:
                continue
            await self._update_join_message(game)

        return True

    async def _list_command(self, context: DiscordMessageContext, _: str) -> bool:
        message = "\n".join(
            f"- [{x.hint}](<{x.link}>)" for x in self._articles[context.message.author.id]
        )
        await context.reply_direct("Your Articles:\n" + message)
        return True

    async def _play_command(self, context: DiscordMessageContext, _: str) -> bool:
        if not isinstance(context.message.channel, discord.TextChannel | discord.Thread):
            await context.reply_direct("Play has to happen in a server channel.")
            return True

        message = await context.reply_all(PLAY_INFO)
        self._watched_message_ids.add(message.id)

        game = Game(context.message.channel, message, set())
        self._games.append(game)

        await message.add_reaction("➕")
        await message.add_reaction("▶️")
        self._logger.info("Preparing game")
        return True

    async def handle_reaction(self, event: discord.RawReactionActionEvent) -> None:
        if event.message_id not in self._watched_message_ids:
            return

        for game in self._games:
            if event.message_id == game.join_message.id:
                await self._process_join(game, event)
            if game.play_message and event.message_id == game.play_message.id:
                await self._process_vote(game, event)

    async def _update_join_message(self, game: Game) -> None:
        active_players = [p.mention for p in game.players if self._articles[p.id]]
        inactive_players = [p.mention for p in game.players if not self._articles[p.id]]
        new_message = (
            PLAY_INFO
            + "\n\n- Players: "
            + ", ".join(active_players)
            + "\n"
            + "- Players (no articles; use `!lie add`): "
            + ", ".join(inactive_players)
        )

        await game.join_message.edit(content=new_message)

    async def _process_join(self, game: Game, event: discord.RawReactionActionEvent) -> None:
        if event.emoji.name == "➕":
            # Can't add players to an already started game
            if game.play_message:
                return

            user = game.channel.guild.get_member(event.user_id)
            if not user:
                return

            if event.event_type == "REACTION_ADD":
                self._logger.info("Adding %s to game in %s", user, game.channel.name)
                game.players.add(user)
            else:
                self._logger.info("Remove %s from game in %s", user, game.channel.name)
                game.players.remove(user)

            await self._update_join_message(game)
            return

        if event.emoji.name == "▶️":
            if game.play_message:
                return

            self._logger.info("Starting game in %s", game.channel.name)

            active = [p for p in game.players if self._articles[p.id]]
            random.shuffle(active)
            self._logger.info("players: %s", active)
            max_articles = min(len(self._articles[p.id]) for p in active)
            articles = {p: random.choices(self._articles[p.id], k=max_articles) for p in active}

            player = random.choice(list(articles.keys()))
            article = random.choice(articles[player])
            self._logger.info("article: %s from %s", article, player)

            game.article = article
            game.correct_player = player

            quips = random.choices(
                [
                    "chaos incarnate",
                    "everyone's favourite",
                    "probably eepy",
                    "looking cute",
                    "tapping on the keyboard",
                    "pondering an orb",
                    "teeing up a joke",
                    "wondering how this works",
                    "reads books y'know",
                ],
                k=len(active),
            )

            intro = [f"{quips[i]} {EMOTES[i]} {p.mention}" for i, p in enumerate(active)]
            intro_text = ", ".join(intro[:-1]) + ", and " + intro[-1]

            message = (
                f"Welcome to '{len(active)-1} of These People Are Lying', because {len(active)-1} "
                f"players will be. I'm Hope Bott; joining me today: {intro_text}."
                f"\nToday's wikipedia article is: **{article.hint}**"
                f"\n-# Emote to indicate who you think is telling the truth."
            )
            game.play_message = await game.channel.send(message)

            for i, _ in enumerate(active):
                await game.play_message.add_reaction(EMOTES[i])

    async def _process_vote(self, game: Game, event: discord.RawReactionActionEvent) -> None:
        index = EMOTES.index(event.emoji.name)
        if not game.active_players or not game.correct_player:
            return

        self._logger.info(
            "Vote for player %d, who is %s. The correct answer is %s",
            index,
            game.active_players[index].name,
            game.correct_player.name,
        )

        # Implement the rest of the game...
