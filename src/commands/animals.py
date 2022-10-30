#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""Animal commands"""

from __future__ import annotations

from typing import Dict

import random
import requests

import bot.commands


class Cat(bot.commands.SimpleCommand):
    def __init__(self) -> None:
        super().__init__("cat")

    def message(self) -> str:
        data = requests.get(url="https://api.thecatapi.com/v1/images/search").json()

        return str(data[0]["url"]) if data else ""


class Dog(bot.commands.SimpleCommand):
    def __init__(self) -> None:
        super().__init__("dog")

    def message(self) -> str:
        data = requests.get(url="https://api.thedogapi.com/v1/images/search").json()

        return str(data[0]["url"]) if data else ""


class Fox(bot.commands.SimpleCommand):
    def __init__(self) -> None:
        super().__init__("fox")

    def message(self) -> str:
        data = requests.get(url="https://randomfox.ca/floof/").json()

        return str(data["image"]) if data else ""


class Bun(bot.commands.SimpleCommand):
    def __init__(self) -> None:
        super().__init__("bun")

    def message(self) -> str:
        data = requests.get(url="https://api.bunnies.io/v2/loop/random/?media=gif,png").json()

        return str(data["media"]["gif"])


class Panda(bot.commands.ParamCommand):
    types: Dict[str, str] = {
        "bamboo": "https://some-random-api.ml/animal/panda",
        "red": "https://some-random-api.ml/animal/red_panda",
        "trash": "https://some-random-api.ml/animal/raccoon",
    }

    def __init__(self) -> None:
        super().__init__("panda", 0, 1)

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

        url = self.types[panda_type]
        data = requests.get(url=url).json()

        if not data:
            return False

        await context.reply_all(data["image"])
        await context.reply_all(data["fact"])
        return True


class Bird(bot.commands.SimpleCommand):
    def message(self) -> str:
        data = requests.get(url="https://some-random-api.ml/animal/bird").json()

        return str(data["image"]) if data else ""
