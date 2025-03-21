# SPDX-FileCopyrightText: 2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""Animal commands"""

from __future__ import annotations as _future_annotations

import random

import aiohttp

import bot.commands


class Animality(bot.commands.SimpleCommand):
    animal: str
    session: aiohttp.ClientSession

    def __init__(self, session: aiohttp.ClientSession, animal: str) -> None:
        super().__init__(animal)
        self.animal = animal
        self.session = session

    @property
    def group(self) -> str | None:
        return "Animals"

    @property
    def help(self) -> str:
        return f"Get a random image of a {self.animal}"

    async def process(self, context: bot.commands.MessageContext, _: str) -> bool:
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
    """Get a random image of a cat."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        super().__init__("cat")
        self.session = session

    @property
    def group(self) -> str | None:
        return "Animals"

    async def message(self) -> str | None:
        response = await self.session.get(url="https://api.thecatapi.com/v1/images/search")
        data = await response.json()

        return str(data[0]["url"]) if data else None


class Dog(bot.commands.SimpleCommand):
    """Get a random image of a dog."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        super().__init__("dog")
        self.session = session

    @property
    def group(self) -> str | None:
        return "Animals"

    async def message(self) -> str:
        response = await self.session.get(url="https://api.thedogapi.com/v1/images/search")
        data = await response.json()

        return str(data[0]["url"]) if data else ""


class Fox(bot.commands.SimpleCommand):
    """Get a random image of a fox."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        super().__init__("fox")
        self.session = session

    @property
    def group(self) -> str | None:
        return "Animals"

    async def message(self) -> str:
        response = await self.session.get(url="https://randomfox.ca/floof/")
        data = await response.json()

        return str(data["image"]) if data else ""


class Bun(bot.commands.SimpleCommand):
    """Get a random image of a rabbit."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        super().__init__("bun")
        self.session = session

    @property
    def group(self) -> str | None:
        return "Animals"

    async def message(self) -> str:
        response = await self.session.get(
            url="https://api.bunnies.io/v2/loop/random/?media=gif,png",
        )
        data = await response.json()

        return str(data["media"]["gif"])


PANDA_TYPES: dict[str, list[str]] = {
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


class Panda(bot.commands.ParamCommand):
    """Get a random image of a giant panda, red panda, or raccoon."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        super().__init__("panda", 0, 1)
        self.session = session

    @property
    def group(self) -> str | None:
        return "Animals"

    async def process_args(self, context: bot.commands.MessageContext, *args: str) -> bool:
        panda_type = args[0] if args else random.choice(list(PANDA_TYPES))

        if panda_type not in PANDA_TYPES:
            await context.reply_all(
                f"Unknown panda type. I can serve {', '. join(PANDA_TYPES)}",
            )
            return True

        url = random.choice(PANDA_TYPES[panda_type])
        response = await self.session.get(url=url)
        data = await response.json()

        if not data:
            return False

        await context.reply_all(data.get("image", data.get("img")))
        await context.reply_all(data["fact"])
        return True


class Bird(bot.commands.SimpleCommand):
    """Get a random image of a bird."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        super().__init__("!bird")
        self.session = session

    @property
    def group(self) -> str | None:
        return "Animals"

    @property
    def command_hint(self) -> str:
        return "!bird"

    def matches(self, message: str) -> bool:
        """Check if this command is matched"""
        return (message.lower() + " ").startswith(("!bird ", "!birb "))

    async def message(self) -> str:
        url = random.choice(
            [
                "https://some-random-api.com/animal/bird",
                "https://api.animality.xyz/img/bird",
            ],
        )

        response = await self.session.get(url=url)
        data = await response.json()

        return str(data.get("image", data.get("img"))) if data else ""
