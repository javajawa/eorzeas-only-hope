#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""Animal commands"""

from __future__ import annotations

import aiohttp
import random

import bot.commands


class Animality(bot.commands.SimpleCommand):
    animal: str
    session: aiohttp.ClientSession

    def __init__(self, session: aiohttp.ClientSession, animal: str) -> None:
        super().__init__(animal)
        self.animal = animal
        self.session = session

    async def process(self, context: bot.commands.MessageContext, message: str) -> bool:
        response = await self.session.get(url=f"https://api.animality.xyz/all/{self.animal}")

        data = await response.json()

        if not data:
            return False

        await context.reply_all(data["image"])
        await context.reply_all(data["fact"])
        return True

    async def message(self) -> str | None:
        return None


class Cat(bot.commands.SimpleCommand):
    def __init__(self, session: aiohttp.ClientSession) -> None:
        super().__init__("cat")
        self.session = session

    async def message(self) -> str | None:
        response = await self.session.get(url="https://api.thecatapi.com/v1/images/search")
        data = await response.json()

        return str(data[0]["url"]) if data else None


class Dog(bot.commands.SimpleCommand):
    def __init__(self, session: aiohttp.ClientSession) -> None:
        super().__init__("dog")
        self.session = session

    async def message(self) -> str:
        response = await self.session.get(url="https://api.thedogapi.com/v1/images/search")
        data = await response.json()

        return str(data[0]["url"]) if data else ""


class Fox(bot.commands.SimpleCommand):
    def __init__(self, session: aiohttp.ClientSession) -> None:
        super().__init__("fox")
        self.session = session

    async def message(self) -> str:
        response = await self.session.get(url="https://randomfox.ca/floof/")
        data = await response.json()

        return str(data["image"]) if data else ""


class Bun(bot.commands.SimpleCommand):
    def __init__(self, session: aiohttp.ClientSession) -> None:
        super().__init__("bun")
        self.session = session

    async def message(self) -> str:
        response = await self.session.get(url="https://api.bunnies.io/v2/loop/random/?media=gif,png")
        data = await response.json()

        return str(data["media"]["gif"])


class Panda(bot.commands.ParamCommand):
    types: dict[str, list[str]] = {
        "bamboo": [
            "https://some-random-api.com/animal/panda",
            "https://api.animality.xyz/all/panda",
        ],
        "red": [
            "https://some-random-api.com/animal/red_panda",
            "https://api.animality.xyz/all/redpanda",
        ],
        "trash": ["https://some-random-api.com/animal/raccoon"],
    }

    def __init__(self, session: aiohttp.ClientSession) -> None:
        super().__init__("panda", 0, 1)
        self.session = session

    async def process_args(self, context: bot.commands.MessageContext, *args: str) -> bool:
        if not args:
            panda_type = random.choice(list(self.types.keys()))
        else:
            panda_type = args[0]

        if panda_type not in self.types:
            await context.reply_all(
                f"Unknown panda type. I can serve {', '. join(self.types)}"
            )
            return True

        url = random.choice(self.types[panda_type])
        response = await self.session.get(url=url)
        data = await response.json()

        if not data:
            return False

        await context.reply_all(data.get("image", data.get("img")))
        await context.reply_all(data["fact"])
        return True


class Bird(bot.commands.SimpleCommand):
    def __init__(self, command: str, session: aiohttp.ClientSession) -> None:
        super().__init__(command)
        self.session = session

    async def message(self) -> str:
        url = random.choice(
            [
                "https://some-random-api.com/animal/bird",
                "https://api.animality.xyz/img/bird",
            ]
        )

        response = await self.session.get(url=url)
        data = await response.json()

        return str(data.get("image", data.get("img"))) if data else ""
