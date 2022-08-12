#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""Self care commands"""

from __future__ import annotations

import requests

import bot.commands

from .order import TeamOrder, TeamOrderDonate, TeamOrderBid, DesertBusOrder


class InspiroBot(bot.commands.SimpleCommand):
    """Grab a random image from Inspiro-Bot"""

    def __init__(self) -> None:
        super().__init__("inspire")

    def message(self) -> str:
        return requests.get(url="https://inspirobot.me/api?generate=true").text


class Beep(bot.commands.SimpleCommand):
    """Do a boop"""

    def __init__(self) -> None:
        super().__init__("beep")

    def message(self) -> str:
        return "*boop*!"


class Boop(bot.commands.SimpleCommand):
    """Do a beep"""

    def __init__(self) -> None:
        super().__init__("boop")

    def message(self) -> str:
        return "*beep*!"


__all__ = [
    "Boop",
    "Beep",
    "TeamOrder",
    "TeamOrderDonate",
    "TeamOrderBid",
    "DesertBusOrder",
]
