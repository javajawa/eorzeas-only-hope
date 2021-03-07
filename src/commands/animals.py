#!/usr/bin/env python3
# vim: ts=4 expandtab

"""Self care commands"""

from __future__ import annotations

from typing import Dict

import random
import requests

import bot.commands


class Cat(bot.commands.SimpleCommand):
    def __init__(self) -> None:
        super().__init__("cat", Cat.message)

    @staticmethod
    def message() -> str:
        data = requests.get(url="https://api.thecatapi.com/v1/images/search").json()

        return str(data[0]["url"]) if data else ""


class Dog(bot.commands.SimpleCommand):
    def __init__(self) -> None:
        super().__init__("dog", Dog.message)

    @staticmethod
    def message() -> str:
        data = requests.get(url="https://api.thedogapi.com/v1/images/search").json()

        return str(data[0]["url"]) if data else ""


class Fox(bot.commands.SimpleCommand):
    def __init__(self) -> None:
        super().__init__("fox", Fox.message)

    @staticmethod
    def message() -> str:
        data = requests.get(url="https://randomfox.ca/floof/").json()

        return str(data["image"]) if data else ""


class Bun(bot.commands.SimpleCommand):
    def __init__(self) -> None:
        super().__init__("bun", Bun.message)

    @staticmethod
    def message() -> str:
        data = requests.get(
            url="https://api.bunnies.io/v2/loop/random/?media=gif,png"
        ).json()

        return str(data["media"]["gif"])


class Panda(bot.commands.ParamCommand):
    types: Dict[str, str] = {
        "bamboo": "https://some-random-api.ml/img/panda",
        "red": "https://some-random-api.ml/img/red_panda",
        "trash": "https://some-random-api.ml/img/racoon",
    }

    def __init__(self) -> None:
        super().__init__("panda", 0, 1)

    async def process_args(
        self, context: bot.commands.MessageContext, *args: str
    ) -> bool:
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

        await context.reply_all(data["link"])
        return True


class Birb(bot.commands.SimpleCommand):
    def __init__(self) -> None:
        super().__init__("birb", Birb.message)

    @staticmethod
    def message() -> str:
        data = requests.get(url="https://some-random-api.ml/img/birb").json()

        return str(data["link"]) if data else ""


class Bird(bot.commands.SimpleCommand):
    def __init__(self) -> None:
        super().__init__("bird", Birb.message)
