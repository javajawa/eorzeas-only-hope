#!/usr/bin/env python3
# vim: ts=4 expandtab nospell

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
import memes.order
import memes.serge
import twitch as twitch_commands

from eorzea.storage import SQLite
from bot import DiscordBot, TwitchBot
from bot.commands import Command, RateLimitCommand


def main() -> None:
    """Run the bots!"""

    with SQLite("list.db") as storage:
        commands: List[Command] = [
            # Memes.
            RateLimitCommand(memes.Belopa(), 5),
            RateLimitCommand(memes.Heresy(), 5),
            RateLimitCommand(memes.InspiroBot(), 15),
            RateLimitCommand(memes.cat.Cat(), 5),
            RateLimitCommand(memes.serge.Sergeism(), 5),
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
            RateLimitCommand(eorzea.GobbieBoom(), 5),
            RateLimitCommand(eorzea.LaHee(), 5),
            RateLimitCommand(eorzea.LaliHo(), 5),
            RateLimitCommand(eorzea.Moogle(), 5),
            RateLimitCommand(eorzea.Scree(), 5),
            RateLimitCommand(eorzea.Wasshoi(), 5),
            # Fake / fun dates.
            RateLimitCommand(timekeeping.March(), 5),
            RateLimitCommand(timekeeping.SMarch(), 5),
            RateLimitCommand(timekeeping.BusIsComing(), 5),
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
