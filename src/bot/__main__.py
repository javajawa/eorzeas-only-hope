#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""Only Hope Bot"""

from __future__ import annotations

from typing import Any, Generator, List

import asyncio
import os
import signal
import yaml

from commands import (
    animals,
    badapple,
    order,
    minecraft,
    prosegen,
    selfcare,
    timekeeping,
    twitch as twitch_commands,
)

import eorzea
import eorzea.lodestone

import ffxiv_quotes

from eorzea.storage import SQLite
from bot import DiscordBot, TwitchBot
from bot.commands import Command, RateLimitCommand, RandomCommand, RegexCommand


def main() -> None:
    """Run the bots!"""
    loop = asyncio.get_event_loop()

    commands: List[Command] = custom_commands(loop)
    commands += list(load_commands_from_yaml())

    loop.add_signal_handler(signal.SIGINT, loop.stop)
    loop.add_signal_handler(signal.SIGTERM, loop.stop)

    with open("twitch.token", "rt", encoding="utf-8") as token_handle:
        [nick, token, *channels] = token_handle.read().strip().split("::")

    irc = TwitchBot(loop, token, nick, commands, channels)
    irc_task = loop.create_task(irc.connect(), name="irc")

    with open("discord.token", "rt", encoding="utf-8") as token_handle:
        token = token_handle.read().strip()

    if not token:
        raise Exception("Unable to load token from token file")

    discord = DiscordBot(loop, commands)
    discord_task = loop.create_task(discord.start(token), name="discord")

    try:
        print("Starting main loop")
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    loop.run_until_complete(irc.close())
    loop.run_until_complete(discord.close())
    loop.run_until_complete(irc_task)
    loop.run_until_complete(discord_task)
    loop.close()


def custom_commands(loop: asyncio.AbstractEventLoop) -> List[Command]:
    commands: List[Command] = []

    # Final Fantasy XIV.
    storage = SQLite("list.db")
    prose_data = ffxiv_quotes.get_ffxiv_quotes(loop, "ALISAIE", "URIANGER")

    commands.extend(
        [
            eorzea.HopeAdder(storage),
            eorzea.OnlyHope(storage),
            eorzea.Party(storage),
            eorzea.Stats(storage),
            eorzea.lodestone.PlayerLookup(),
            prosegen.ProseGenCommand("alisaie", prose_data["ALISAIE"]),
            prosegen.ProseGenCommand("urianger", prose_data["URIANGER"]),
        ]
    )

    # Memes.
    commands.extend(
        [
            order.TeamOrder(),
            order.TeamOrderBid(),
            order.TeamOrderDonate(),
            order.DesertBusOrder(),
            badapple.BadAppleCommand(),
        ]
    )

    # Animals.
    commands.extend(
        [
            RateLimitCommand(animals.Cat(), 2),
            RateLimitCommand(animals.Dog(), 2),
            RateLimitCommand(animals.Fox(), 2),
            RateLimitCommand(animals.Bun(), 2),
            RateLimitCommand(animals.Bird("bird"), 2),
            RateLimitCommand(animals.Bird("birb"), 2),
            RateLimitCommand(animals.Panda(), 2),
        ]
    )

    # Minecraft.
    commands.extend(
        [
            minecraft.Pillars(),
            minecraft.Stack(),
            minecraft.NetherLocation(),
            minecraft.OverworldLocation(),
        ]
    )

    # Self care.
    commands.extend(
        [
            selfcare.BadSelfCare(),
        ]
    )

    # Fake / fun dates.
    commands.extend(
        [
            RateLimitCommand(timekeeping.March(), 2),
            RateLimitCommand(timekeeping.BusIsComing(), 2),
            RateLimitCommand(timekeeping.BusStop(), 2),
        ]
    )

    # Twitch commands for sugarsh0t.
    commands.extend(
        [
            twitch_commands.SassPlan(),
            twitch_commands.Cardinal(),
        ]
    )

    return commands


def load_commands_from_yaml() -> Generator[Command, None, None]:
    cwd = os.curdir
    command_dir = os.path.join(cwd, "commands")

    for file in os.listdir(command_dir):
        if not file.endswith(".yaml"):
            continue

        path = os.path.join(command_dir, file)

        with open(path, "rb") as stream:
            for block in yaml.load_all(stream, yaml.CSafeLoader):
                yield from load_command(block)


def load_command(data: Any) -> Generator[Command, None, None]:
    if not isinstance(data, dict):
        return

    if "commands" in data:
        yield RandomCommand(
            data.get("commands", []), data.get("formats", []), data.get("args", {})
        )

    if "regexp" in data:
        if isinstance(data["regexp"], str):
            yield RegexCommand(data["regexp"], data.get("formats", []), data.get("args", {}))


if __name__ == "__main__":
    main()
