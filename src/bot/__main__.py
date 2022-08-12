#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""Only Hope Bot"""

from __future__ import annotations

from typing import List

import asyncio
import signal

from commands import (
    animals,
    memes,
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
from bot.commands import Command, RateLimitCommand


def main() -> None:
    """Run the bots!"""

    prose_data = ffxiv_quotes.get_ffxiv_quotes("ALISAIE", "URIANGER")

    with SQLite("list.db") as storage:
        commands: List[Command] = [
            # Memes.
            RateLimitCommand(memes.Belopa(), 2),
            RateLimitCommand(memes.Heresy(), 2),
            memes.TeamOrder(),
            memes.TeamOrderBid(),
            memes.TeamOrderDonate(),
            memes.DesertBusOrder(),
            memes.Boop(),
            memes.Beep(),
            # Animals.
            RateLimitCommand(animals.Cat(), 2),
            RateLimitCommand(animals.Dog(), 2),
            RateLimitCommand(animals.Fox(), 2),
            RateLimitCommand(animals.Bun(), 2),
            RateLimitCommand(animals.Birb(), 2),
            RateLimitCommand(animals.Bird(), 2),
            RateLimitCommand(animals.Panda(), 2),
            # Minecraft.
            minecraft.Pillars(),
            minecraft.Stack(),
            minecraft.NetherLocation(),
            minecraft.OverworldLocation(),
            # Self care.
            selfcare.BusCare(),
            selfcare.SelfCare(),
            selfcare.BadSelfCare(),
            selfcare.SelfCute(),
            selfcare.SelfCute("selfcat"),
            selfcare.SelfCute("selfbun"),
            selfcare.SelfChair(),
            selfcare.ShelfCare(),
            selfcare.ShelfCute(),
            selfcare.ShelfCat(),
            selfcare.ShelfChair(),
            selfcare.Sticky(),
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
            prosegen.ProseGenCommand("alisaie", prose_data["ALISAIE"]),
            prosegen.ProseGenCommand("urianger", prose_data["URIANGER"]),
            # Fake / fun dates.
            RateLimitCommand(timekeeping.March(), 2),
            RateLimitCommand(timekeeping.SMarch(), 2),
            RateLimitCommand(timekeeping.BusIsComing(), 2),
            RateLimitCommand(timekeeping.BusStop(), 2),
            # Twitch commands for sugarsh0t.
            twitch_commands.Plan(),
            twitch_commands.Warnings(),
            twitch_commands.SassPlan(),
            twitch_commands.Cardinal(),
        ]
        discord_commands: List[Command] = [eorzea.HopeAdder(storage)]

        loop = asyncio.get_event_loop()
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

        discord = DiscordBot(loop, discord_commands + commands)
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
        loop.run_until_complete(irc._connection._keeper)
        loop.close()


if __name__ == "__main__":
    main()
