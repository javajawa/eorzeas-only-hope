#!/usr/bin/env python3
# vim: ts=4 expandtab

"""Final Fantasy XIV commands"""

from __future__ import annotations

from typing import Dict, List, Tuple
from collections import defaultdict

import datetime
import requests
import discord

import bot.commands

from bot.discord import DiscordMessageContext


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
    key: str

    def __init__(self) -> None:
        super().__init__("lodestone", 1, 3)

        with open("lodestone.token", "rt", encoding="utf-8") as token:
            self.key = token.read().strip()

    async def process_args(self, context: bot.commands.MessageContext, *args: str) -> bool:
        if not isinstance(context, DiscordMessageContext):
            return False

        if len(args) > 1 or not args[0].isnumeric():
            results = await self.search(args, context)
        else:
            results = [int(args[0])]

        for character_id in results:
            data = requests.get("https://xivapi.com/character/" + str(character_id)).json()

            embed = discord.Embed(
                title=data["Character"]["Name"],
                url="https://eu.finalfantasyxiv.com/lodestone/character/" + str(character_id),
                timestamp=datetime.datetime.utcfromtimestamp(data["Character"]["ParseDate"]),
            )
            embed.set_thumbnail(url=data["Character"]["Avatar"])
            embed.set_image(url=data["Character"]["Portrait"])
            embed.add_field(name="Server", value=data["Character"]["Server"])

            await context.reply_all(embed)

        return True

    async def search(
        self, args: Tuple[str, ...], context: DiscordMessageContext
    ) -> List[int]:
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

        return await self.run_search(context, name, server, force_all)

    async def run_search(
        self,
        context: DiscordMessageContext,
        name: str,
        server: str,
        force_all: bool,
    ) -> List[int]:
        results = requests.get(
            "https://xivapi.com/character/search",
            params={"name": name, "server": server, "private_key": self.key},
        ).json()

        total = results["Pagination"]["ResultsTotal"]
        if total < len(results["Results"]):
            total = len(results["Results"])

        if total < 3:
            return [x["ID"] for x in results["Results"]]

        exact = {
            x["Server"]: x["ID"] for x in results["Results"] if x["Name"].lower() == name
        }

        if len(exact) < 3 and total <= 50:
            return list(exact.values())

        to_return = [
            v
            for k, v in exact.items()
            if k.startswith("Adamantoise") or k.startswith("Siren")
        ]

        if to_return and not force_all:
            if len(exact) > len(to_return):
                await context.reply_all(
                    f"Found {len(exact)} exact, {total} approximate matches, "
                    f"returning only Siren and Adamantoise. Use [all] to see more"
                )

            return to_return

        characters: Dict[str, List[str]] = defaultdict(list)

        for character in results["Results"]:
            characters[character["Server"]].append(f"{character['Name']} `{character['ID']}`")

        message = "\n".join(["**" + k + "**\n" + "\n".join(v) for k, v in characters.items()])
        message = message[:1900] + "..." if len(message) > 1950 else message

        await context.reply_all(
            f"Found {total} matches, please be more specific:\n" + message
        )

        return []
