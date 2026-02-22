# SPDX-FileCopyrightText: 2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""Only Hope Bot"""

from __future__ import annotations as _future_annotations

from collections.abc import Generator

import asyncio
import logging
import pathlib
import signal
import sqlite3

import aiohttp
import yaml

import eorzea
from bot import DiscordBot, TwitchBot, role_manager
from bot.commands import Command
from bot.random import RandomCommand

# noinspection PyCompatibility
from commands import (
    animals,
    badapple,
    convert,
    desertbus,
    inspiro,
    minecraft,
    order,
    selfcare,
    technical_difficulties,
    timekeeping,
    weather,
    wisdom,
)
from eorzea.storage import SQLite


def main() -> None:
    """Run the bots!"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    logger = logging.getLogger("hopebot")
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)

    session = aiohttp.ClientSession(loop=loop, raise_for_status=True)

    airlock = role_manager.AirLock(logger, sqlite3.connect("discord_users.db"))
    roles = role_manager.RoleReactionHandler(logger)

    commands: list[Command] = [airlock, roles]
    commands += custom_commands(loop, session)
    commands += list(load_commands_from_yaml())

    loop.add_signal_handler(signal.SIGINT, loop.stop)
    loop.add_signal_handler(signal.SIGTERM, loop.stop)

    [nick, token, *channels] = (
        pathlib.Path("twitch.token").read_text(encoding="utf-8").strip().split("::")
    )

    irc = TwitchBot(loop, logger.getChild("twitch"), token, nick, commands, channels)
    irc_task = loop.create_task(irc.connect(), name="irc")

    token = pathlib.Path("discord.token").read_text(encoding="utf-8").strip()

    if not token:
        raise OSError("Unable to load token from token file")

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
    if airlock.activity_task:
        airlock.activity_task.cancel()
        loop.run_until_complete(airlock.activity_task)
    loop.close()


def custom_commands(
    loop: asyncio.AbstractEventLoop,
    session: aiohttp.ClientSession,
) -> list[Command]:
    commands: list[Command] = []

    # Final Fantasy XIV.
    storage = SQLite("list.db")

    commands.extend(
        [
            eorzea.HopeAdder(storage),
            eorzea.OnlyHope(storage),
            eorzea.Party(storage),
            eorzea.Stats(storage),
        ],
    )

    # Interactive Commands
    weather_token = pathlib.Path("weather.token").read_text(encoding="utf-8")
    commands.extend(
        [
            weather.Weather(session, weather_token),
            badapple.BadAppleCommand(),
            convert.ConvertorBot(logging.getLogger("conversions")),
            inspiro.InspiroBot(session),
            technical_difficulties.PeopleAreLying(session),
        ],
    )

    # Animals.
    commands.extend(
        [
            animals.Cat(session),
            animals.Dog(session),
            animals.Fox(session),
            animals.Bun(session),
            animals.Bird(session),
            animals.Panda(session),
            animals.Raccoon(session),
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
            animals.Animality(session, "hedgehog"),
            animals.Animality(session, "turtle"),
            animals.Animality(session, "narwhal"),
            animals.Animality(session, "squirrel"),
            animals.Animality(session, "fish"),
            animals.Animality(session, "horse"),
        ],
    )

    # Minecraft.
    commands.extend(
        [
            minecraft.Pillars(),
            minecraft.Stack(),
            minecraft.NetherLocation(),
            minecraft.OverworldLocation(),
            weather.TemperatureCommand(),
        ],
    )

    # Complex Random Commands
    commands.extend(
        [
            selfcare.BadSelfCare(),
            wisdom.Wisdom(),
        ],
    )

    # Pandini
    commands.extend(
        [
            timekeeping.March(),
            timekeeping.March("truemarch"),
            timekeeping.WhenMarch(),
        ],
    )

    # Charity and Fundraisers
    commands.extend(
        [
            order.TeamOrder(),
            order.TeamOrderBid(),
            order.TeamOrderDonate(),
            desertbus.DesertBusOrder(session),
            desertbus.VSTSearch(loop, session),
            desertbus.BusIsComing(),
            desertbus.BusStop(session),
        ],
    )

    return commands


def load_commands_from_yaml() -> Generator[Command, None, None]:
    cwd = pathlib.Path.cwd()
    command_dir = cwd / "commands"

    for file in command_dir.iterdir():
        if not file.name.endswith(".yaml"):
            continue

        with file.open("rb") as stream:
            for block in yaml.load_all(stream, yaml.CSafeLoader):
                yield RandomCommand(block)


if __name__ == "__main__":
    main()
