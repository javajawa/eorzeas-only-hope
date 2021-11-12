#!/usr/bin/env python3

"""Minecraft Bot Commands"""

from __future__ import annotations

import math

import bot.commands
from bot.commands import MessageContext


class Pillars(bot.commands.ParamCommand):
    """Calculates even pillar arrangement for Minecraft"""

    def __init__(self) -> None:
        super().__init__("pillars", 1, 2)

    async def process_args(self, context: bot.commands.MessageContext, *args: str) -> bool:
        """Calculate the pillars"""

        length = int(args[0])
        width = int(args[1]) if len(args) > 1 else 1

        if length < 3:
            return False

        if width >= length:
            return False

        valid = []

        for gap in range(width + 1, math.ceil(length / 2 - width)):
            count = math.ceil(length / gap)

            if count * gap - width == length:
                valid.append(f"{count - 1} pillars {gap - width} blocks apart")

            if count % 2 == 1 and count * gap - width == length - 1:
                valid.append(
                    f"{count - 1} pillars {gap - width} blocks apart, with extra centre block"
                )

        if not valid:
            await context.reply_all(
                f"No complete solutions for pillars of width {width} spanning {length}"
            )

            return True

        await context.reply_all(
            f"For pillars of {width} blocks spanning {length} blocks: {'; '.join(valid)}"
        )

        return True


class NetherLocation(bot.commands.ParamCommand):
    """Converts an nether location to a over world location."""

    def __init__(self) -> None:
        super().__init__("nether", 1, 9)

    async def process_args(self, context: MessageContext, *args: str) -> bool:
        """Converts an nether location to a over world location."""

        output = []

        for datum in args:
            datum = datum.strip().strip(",")

            if datum.isnumeric():
                output.append(math.floor(8 * int(datum)))

        if not output:
            return False

        await context.reply_all(f"Over-world Location: {', '.join([str(x) for x in output])}")

        return True


class OverworldLocation(bot.commands.ParamCommand):
    """Converts an over world location to a nether location."""

    def __init__(self) -> None:
        super().__init__("overworld", 1, 9)

    async def process_args(self, context: MessageContext, *args: str) -> bool:
        """Converts an over world location to a nether location."""

        output = []

        for datum in args:
            datum = datum.strip().strip(",")

            if datum.isnumeric():
                output.append(math.floor(int(datum) / 8))

        if not output:
            return False

        await context.reply_all(f"Nether Location: {', '.join([str(x) for x in output])}")

        return True
