#!/usr/bin/python3
# vim: ts=4 expandtab

"""Only Hope Bot"""

from __future__ import annotations

from typing import List

from multiprocessing import Process

import eorzea
import minecraft
import selfcare
import timekeeping
import memes
import memes.cat
import twitch as twitch_commands

from eorzea.storage import SQLite
from bot import DiscordBot, TwitchBot
from bot.commands import Command, RateLimitCommand


def main() -> None:
    """Run the bots!"""

    with SQLite("list.db") as storage:
        commands: List[Command] = [
            memes.TeamOrder(),
            selfcare.SelfCare(),
            selfcare.SelfCute(),
            selfcare.SelfCute("selfcat"),
            eorzea.OnlyHope(storage),
            eorzea.Party(storage),
            eorzea.Stats(storage),
            twitch_commands.Plan(),
            twitch_commands.SassPlan(),
            RateLimitCommand(timekeeping.March(), 90),
            RateLimitCommand(timekeeping.BusIsComing(), 90),
            RateLimitCommand(memes.cat.Cat(), 10),
            RateLimitCommand(eorzea.GobbieBoom(), 10),
            RateLimitCommand(eorzea.LaHee(), 10),
            RateLimitCommand(eorzea.LaliHo(), 10),
            RateLimitCommand(eorzea.Scree(), 10),
            RateLimitCommand(eorzea.Wasshoi(), 10),
            minecraft.Pillars(),
            minecraft.NetherLocation(),
            minecraft.OverworldLocation(),
        ]
        discord_commands: List[Command] = [eorzea.HopeAdder(storage)]

        twitch = Process(target=twitch_bot, args=(commands,))
        discord = Process(target=discord_bot, args=(discord_commands + commands,))

        discord.start()
        twitch.start()

        try:
            twitch.join()
            discord.join()
        except KeyboardInterrupt:
            twitch.terminate()
            discord.terminate()


def twitch_bot(commands: List[Command]) -> None:
    """Launch the Twitch bot"""
    with open("twitch.token") as token_handle:
        [nick, token, *channels] = token_handle.read().strip().split("::")

    instance = TwitchBot(token, nick, commands, channels)
    instance.run()


def discord_bot(commands: List[Command]) -> None:
    """Launch the Discord bot"""
    with open("discord.token") as token_handle:
        token = token_handle.read().strip()

    if not token:
        raise Exception("Unable to load token from token file")

    instance = DiscordBot(commands)
    instance.run(token)


if __name__ == "__main__":
    main()
