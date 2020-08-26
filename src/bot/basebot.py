#!/usr/bin/python3
# vim: ts=4 expandtab

from __future__ import annotations

from typing import Any

import abc
import re

from storage import DataStore
from eorzea import get_single_quote, get_party_quote


class BaseBot(abc.ABC):
    storage: DataStore
    pattern: re.Pattern  # type: ignore
    calls: int

    def __init__(self: BaseBot, storage: DataStore):
        super().__init__()

        self.storage = storage
        self.pattern = re.compile(
            " you[^ ]*( are)? [^ ]+zea'?s only hope", re.IGNORECASE
        )
        self.calls = 0

    async def process(self: BaseBot, message: str, ctx: Any) -> None:
        name: str = ""

        if message.lower() == "!onlyhope":
            self.calls += 1
            name = self.storage.random()

            await self.reply_all(ctx, get_single_quote(name))
            return

        if message.lower() == "!stats":
            await self.show_stats(ctx)
            return

        if message.lower().startswith("!party"):
            await self.party_command(message, ctx)
            return

        for line in message.split("\n"):
            if self.pattern.search(line):
                [name, _] = message.split(" you", 1)
            elif line.lower().startswith("!onlyhope"):
                name = line[9:]

            await self.add_name(name, ctx)

    async def show_stats(self: BaseBot, ctx: Any) -> None:
        await self.reply_all(
            ctx, f"Omega has tested {self.calls} of {len(self.storage)} souls"
        )

    async def add_name(self: BaseBot, name: str, ctx: Any) -> None:
        # TODO: remove all punctuation etc?
        name = name.strip()

        if not name:
            return

        if self.storage.add(name):
            await self.react(ctx)

    async def party_command(self: BaseBot, message: str, ctx: Any) -> bool:
        size: int = 4
        [*args] = message.split(" ")

        if len(args) > 3:
            return False

        try:
            if args[0].lower() != "!party":
                size = int(args[0][6:])

            if len(args) == 2:
                size = int(args[1])
        except ValueError:
            return False

        if not size:
            return False

        self.calls += 1
        names = [self.storage.random() for _ in range(min(size, 24))]

        await self.reply_all(ctx, get_party_quote(names))

        return True

    @abc.abstractmethod
    async def reply_all(self: BaseBot, ctx: Any, message: str) -> None:
        pass

    @abc.abstractmethod
    async def react(self: BaseBot, ctx: Any) -> None:
        pass
