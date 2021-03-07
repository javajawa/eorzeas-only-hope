#!/usr/bin/env python3
# vim: ts=4 expandtab nospell

"""Only Hope Bot"""

from __future__ import annotations

from typing import List

from multiprocessing import Process

import animals
import eorzea
import eorzea.lodestone
import memes
import memes.order
import minecraft
import selfcare
import timekeeping
import twitch as twitch_commands

from eorzea.storage import SQLite
from bot import DiscordBot, TwitchBot
from bot.commands import Command, RateLimitCommand


def main() -> None:
    """Run the bots!"""

    with SQLite("list.db") as storage:
        commands: List[Command] = [
            # Memes.
            RateLimitCommand(memes.Belopa(), 2),
            RateLimitCommand(memes.Heresy(), 2),
            RateLimitCommand(animals.Cat(), 2),
            RateLimitCommand(animals.Dog(), 2),
            RateLimitCommand(animals.Fox(), 2),
            RateLimitCommand(animals.Bun(), 2),
            RateLimitCommand(animals.Birb(), 2),
            RateLimitCommand(animals.Bird(), 2),
            RateLimitCommand(animals.Panda(), 2),
            memes.order.TeamOrder(),
            # Minecraft.
            minecraft.Pillars(),
            minecraft.NetherLocation(),
            minecraft.OverworldLocation(),
            # Self care.
            selfcare.BusCare(),
            selfcare.SelfCare(),
            selfcare.SelfCute(),
            selfcare.SelfCute("selfcat"),
            # Final Fantasy XIV (characters).
            eorzea.OnlyHope(storage),
            eorzea.Party(storage),
            eorzea.Stats(storage),
            # Final Fantasy XIV (memes).
            RateLimitCommand(eorzea.GobbieBoom(), 2),
            RateLimitCommand(eorzea.LaHee(), 2),
            RateLimitCommand(eorzea.LaliHo(), 2),
            RateLimitCommand(eorzea.Moogle(), 2),
            RateLimitCommand(eorzea.Scree(), 2),
            RateLimitCommand(eorzea.Wasshoi(), 2),
            eorzea.lodestone.PlayerLookup(),
            # Fake / fun dates.
            RateLimitCommand(timekeeping.March(), 2),
            RateLimitCommand(timekeeping.SMarch(), 2),
            RateLimitCommand(timekeeping.BusIsComing(), 2),
            # Twitch commands for sugarsh0t.
            twitch_commands.Plan(),
            twitch_commands.SassPlan(),
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
