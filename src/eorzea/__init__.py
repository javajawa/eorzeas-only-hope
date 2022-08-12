#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""Final Fantasy XIV commands"""

from __future__ import annotations

from typing import List

import random
import re

from bot.commands import MessageContext
from eorzea.storage import DataStore
import bot.commands

PARTY_QUOTES = [
    "{names} are pray returning to the Waking Sands",
    "{names} are pray returning to the Waking Sands",
    "{names} are pray returning to the Waking Sands",
    "{names} are pray returning to the Waking Sands",
    "{names} are pray returning to the Waking Sands",
    "{leader} has been captured by the Garleans. Can {followers} save them?",
    "{leader} has been captured by the Garleans. Can {followers} save them?",
    "{leader} has been captured by the Garleans. Can {followers} save them?",
    "{leader} has been captured by the Garleans. Can {followers} save them?",
    "{leader} has been captured by the Garleans. Can {followers} save them?",
    "Hail the Scions of the Eight Dawn: {names}",
    "Hail the Scions of the Eight Dawn: {names}",
    "Hail the Scions of the Eight Dawn: {names}",
    "Omega is testing {names} in the rift.",
]

SINGLE_QUOTES = [
    "{name}, you are Eorzea's only hope!",
    "{name}, you are Eorzea's only hope!",
    "{name}, you are Eorzea's only hope!",
    "{name}, you are Eorzea's only hope!",
    "{name}, you are Eorzea's only hope!",
    "{name}, you are Eorzea's only hope!",
    "{name}, you are Eorzea's only hope!",
    "{name}, you are Eorzea's only hope!",
    "{name}, you are Eorzea's only hope!",
    "{name}, you are Eorzea's only hope!",
    "{name}, you are the Namazu's only hope!",
    "{name}, you are the Namazu's only hope!",
    "{name}, you are the Namazu's only hope!",
    "{name} is a cat, a kitty cat. And they dance dance dance, and they dance dance dance",
    "Warrior of Light {name} rides again!",
    "Help me {name}, you're my only hope!",
]

COMMANDS = 0


class Stats(bot.commands.SimpleCommand):
    """!onlyhope yields one name"""

    _data: DataStore

    def __init__(self, data: DataStore):
        super().__init__("stats")
        self._data = data

    def message(self) -> str:
        return f"Omega has tested {len(self._data.seen)} of {len(self._data)} souls"


class HopeAdder(bot.commands.Command):
    """!onlyhope can add names"""

    _storage: DataStore
    _pattern: re.Pattern[str]

    def __init__(self, data: DataStore):
        self._storage = data
        self._pattern = re.compile(" you[^ ]*(?: are)? [^ ]+zea'?s only hope", re.IGNORECASE)

    def matches(self, message: str) -> bool:
        """Checks if this message is a candidate for having a new hero"""
        if self._pattern.search(message):
            return True

        return any(x for x in message.split("\n") if x.startswith("!onlyhope "))

    async def process(self, context: MessageContext, message: str) -> bool:
        """Handle the command in the message"""
        name = ""
        result = False

        for line in message.split("\n"):
            if self._pattern.search(line):
                [name, _] = message.split(" you", 1)
            elif line.lower().startswith("!onlyhope"):
                name = line[9:]

            name = name.strip()

            if not name:
                continue

            result = True
            if self._storage.add(name, context.sender(), context.channel()):
                await context.react()

        return result


class OnlyHope(bot.commands.SimpleCommand):
    """!onlyhope yields one name"""

    _data: DataStore

    def __init__(self, data: DataStore):
        super().__init__("onlyhope")
        self._data = data

    def message(self) -> str:
        return random.choice(SINGLE_QUOTES).format(name=self._data.random().name)


class Party(bot.commands.ParamCommand):
    """!party shows off a group of people"""

    _storage: DataStore

    def __init__(self, data: DataStore):
        super().__init__("party", 0, 1)

        self._storage = data

    async def process_args(self, context: MessageContext, *args: str) -> bool:
        """Generates a party of between 2 and 24"""

        if args and args[0].isnumeric():
            count = max(2, min(int(args[0]), 128))
        else:
            count = 4

        names = [self._storage.random() for _ in range(count)]

        leader: str = names[0].name
        followers: str = combine_name_list([x.name for x in names[1:]])
        name: str = combine_name_list([x.name for x in names])

        message = random.choice(PARTY_QUOTES).format(
            names=name, leader=leader, followers=followers
        )

        await context.reply_all(message[0:1998])

        return True


def combine_name_list(names: List[str]) -> str:
    """Combines a list of names in the English comma, and format."""
    if len(names) == 1:
        return names[0]

    return ", ".join(names[:-1]) + ", and " + names[-1]
