# SPDX-FileCopyrightText: 2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""Final Fantasy XIV commands"""

from __future__ import annotations as _future_annotations

import datetime
import http
import pathlib
from collections import defaultdict

import aiohttp
import discord

import bot.commands
from bot.discord import DiscordMessageContext

MAX_PROFILES_DISPLAYED = 2
MAX_NAME_LIST = 50
MAX_MESSAGE_LENGTH = 2000

DC_LIST = [
    "chaos",
    "light",
    "aether",
    "primal",
    "crystal",
    "elemental",
    "gaia",
    "mana",
]


class PlayerLookup(bot.commands.ParamCommand):
    """Lookup a player name in Lodestone."""

    key: str
    session: aiohttp.ClientSession

    def __init__(self, session: aiohttp.ClientSession) -> None:
        super().__init__("lodestone", 1, 3)

        with pathlib.Path("lodestone.token").open(encoding="utf-8") as token:
            self.key = token.read().strip()

        self.session = session

    @property
    def group(self) -> str:
        return "Eorzea's Only Hope"

    @property
    def command_hint(self) -> str:
        return "!lodestone {name}` or `!lodestone {name} [{server}]"

    async def process_args(self, context: bot.commands.MessageContext, *args: str) -> bool:
        if not isinstance(context, DiscordMessageContext):
            return False

        if len(args) > 1 or not args[0].isnumeric():
            results = await self.search(args, context)
        else:
            results = [int(args[0])]

        for character_id in results:
            response = await self.session.get(
                "https://xivapi.com/character/" + str(character_id),
            )
            data = await response.json()

            embed = discord.Embed(
                title=data["Character"]["Name"],
                url="https://eu.finalfantasyxiv.com/lodestone/character/" + str(character_id),
                timestamp=datetime.datetime.fromtimestamp(
                    data["Character"]["ParseDate"],
                    datetime.UTC,
                ),
            )
            embed.set_thumbnail(url=data["Character"]["Avatar"])
            embed.set_image(url=data["Character"]["Portrait"])
            embed.add_field(name="Server", value=data["Character"]["Server"])

            await context.reply_all(embed)

        return True

    async def search(
        self,
        args: tuple[str, ...],
        context: DiscordMessageContext,
    ) -> list[int]:
        server = ""
        name = ""

        for arg in args:
            if arg.startswith("[") and arg.endswith("]"):
                server = arg[1:-1].lower()
            else:
                name += " " + arg

        if server in DC_LIST:
            server = "_dc_" + server

        name = name.strip().lower()

        force_all = server == "all"

        if force_all:
            server = ""

        return await self.run_search(context, name, server, force_all=force_all)

    async def run_search(
        self,
        context: DiscordMessageContext,
        name: str,
        server: str,
        *,
        force_all: bool,
    ) -> list[int]:
        response = await self.session.get(
            "https://xivapi.com/character/search",
            params={"name": name, "server": server, "private_key": self.key},
        )

        if response.status != http.HTTPStatus.OK:
            return []

        results = await response.json()

        total = results["Pagination"]["ResultsTotal"]
        total = max(total, len(results["Results"]))

        if total <= MAX_PROFILES_DISPLAYED:
            return [x["ID"] for x in results["Results"]]

        exact = {x["Server"]: x["ID"] for x in results["Results"] if x["Name"].lower() == name}

        if len(exact) <= MAX_PROFILES_DISPLAYED and total <= MAX_NAME_LIST:
            return list(exact.values())

        to_return = [v for k, v in exact.items() if k.startswith(("Adamantoise", "Siren"))]

        if to_return and not force_all:
            if len(exact) > len(to_return):
                await context.reply_all(
                    f"Found {len(exact)} exact, {total} approximate matches, "
                    f"returning only Siren and Adamantoise. Use [all] to see more",
                )

            return to_return

        characters: dict[str, list[str]] = defaultdict(list)

        for character in results["Results"]:
            characters[character["Server"]].append(f"{character['Name']} `{character['ID']}`")

        message = "\n".join(["**" + k + "**\n" + "\n".join(v) for k, v in characters.items()])
        message = (
            message[: MAX_MESSAGE_LENGTH - 4] + "..."
            if len(message) > MAX_MESSAGE_LENGTH
            else message
        )

        await context.reply_all(
            f"Found {total} matches, please be more specific:\n" + message,
        )

        return []
