#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""Only Hope Bot"""

from __future__ import annotations

import logging
from typing import Any, Generator, List

import asyncio
import os
import signal
import yaml

import aiohttp

# noinspection PyCompatibility
from commands import (
    animals,
    badapple,
    order,
    minecraft,
    selfcare,
    timekeeping,
    twitch as twitch_commands,
    weather,
)

import eorzea

import ffxiv_quotes

from eorzea.storage import SQLite
from bot import DiscordBot, TwitchBot
from bot.commands import Command
from bot.random import RandomCommand, RegexCommand


def main() -> None:
    """Run the bots!"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    logger = logging.getLogger("hopebot")
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)

    session = aiohttp.ClientSession(loop=loop, raise_for_status=True)

    commands: List[Command] = custom_commands(loop, session)
    commands += list(load_commands_from_yaml())

    loop.add_signal_handler(signal.SIGINT, loop.stop)
    loop.add_signal_handler(signal.SIGTERM, loop.stop)

    with open("twitch.token", "rt", encoding="utf-8") as token_handle:
        [nick, token, *channels] = token_handle.read().strip().split("::")

    irc = TwitchBot(loop, logger.getChild("twitch"), token, nick, commands, channels)
    irc_task = loop.create_task(irc.connect(), name="irc")

    with open("discord.token", "rt", encoding="utf-8") as token_handle:
        token = token_handle.read().strip()

    if not token:
        raise IOError("Unable to load token from token file")

    discord = DiscordBot(logger.getChild("discord"), loop, commands)
    discord_task = loop.create_task(discord.start(token), name="discord")

    try:
        logger.info("Starting main loop")
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    loop.run_until_complete(irc.close())
    loop.run_until_complete(discord.close())
    loop.run_until_complete(irc_task)
    loop.run_until_complete(discord_task)
    loop.run_until_complete(session.close())
    loop.close()


def custom_commands(loop: asyncio.AbstractEventLoop, session: aiohttp.ClientSession) -> List[Command]:
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
            eorzea.ProseGenCommand("alisaie", prose_data["ALISAIE"], storage),
            eorzea.ProseGenCommand("urianger", prose_data["URIANGER"], storage),
        ]
    )

    # Memes.
    commands.extend(
        [
            order.TeamOrder(),
            order.TeamOrderBid(),
            order.TeamOrderDonate(),
            order.DesertBusOrder(session),
            badapple.BadAppleCommand(),
        ]
    )

    # Animals.
    commands.extend(
        [
            animals.Cat(session),
            animals.Dog(session),
            animals.Fox(session),
            animals.Bun(session),
            animals.Bird("bird", session),
            animals.Bird("birb", session),
            animals.Panda(session),
            animals.Animality(session, "koala"),
            animals.Animality(session, "whale"),
            animals.Animality(session, "dolphin"),
            animals.Animality(session, "kangaroo"),
            animals.Animality(session, "lion"),
            animals.Animality(session, "bear"),
            animals.Animality(session, "frog"),
            animals.Animality(session, "duck"),
            animals.Animality(session, "penguin"),
            animals.Animality(session, "axolotl"),
            animals.Animality(session, "capybara"),
        ]
    )

    # Minecraft.
    commands.extend(
        [
            minecraft.Pillars(),
            minecraft.Stack(),
            minecraft.NetherLocation(),
            minecraft.OverworldLocation(),
            weather.TemperatureCommand(),
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
            timekeeping.March(),
            timekeeping.March("truemarch"),
            timekeeping.WhenMarch(),
            timekeeping.BusIsComing(),
            timekeeping.BusStop(session),
        ]
    )

    # Twitch commands for sugarsh0t.
    commands.extend(
        [
            twitch_commands.SassPlan(),
            twitch_commands.Cardinal(),
        ]
    )

    with open("weather.token", encoding="utf-8") as token:
        commands.append(weather.Weather(session, token.read()))

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
            data.get("commands", []),
            data.get("formats", []),
            data.get("args", {}),
            data.get("channels", []),
        )

    if "regexp" in data:
        if isinstance(data["regexp"], str):
            yield RegexCommand(
                data["regexp"],
                data.get("formats", []),
                data.get("args", {}),
                data.get("channels", []),
            )


if __name__ == "__main__":
    main()
