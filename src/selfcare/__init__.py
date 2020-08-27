#!/usr/bin/python3
# vim: ts=4 expandtab

"""Self care commands"""

from __future__ import annotations

import random

import bot.commands

BIG_REMINDERS = [
    "take you meds",
    "check your medication",
]

REGULAR_THINGS = [
    "eat a meal",
    "drink some water",
    "stretch your body",
    "raise you heart rate",
]

DAILY_THINGS = [
    "reach out to someone",
    "tend to a living/growing thing",
    "take a shower/bath",
    "clean one space or surface",
]

FORMATS = [
    "Looking after yourself is key: {reminder}, {regular}, and consider {daily}. 💜",
    "Time to {regular}? Maybe {daily}? Also, {reminder}. 🧡",
]


class SelfCare(bot.commands.SimpleCommand):
    """Reminds our dear friends to look after themselves."""

    def __init__(self):
        super().__init__("selfcare", SelfCare.message)

    @staticmethod
    def message() -> str:
        layout = random.choice(FORMATS)
        reminder = random.choice(BIG_REMINDERS)
        regular = random.choice(REGULAR_THINGS)
        daily = random.choice(DAILY_THINGS)

        return layout.format(reminder=reminder, regular=regular, daily=daily)
