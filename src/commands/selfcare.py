#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""Self care commands"""

from __future__ import annotations

import random

import bot.commands

# Bad Selfcare Actions
BAD_SELF_CARE_IDEAS = list(
    {
        "watch": "cute cat videos",
        "eat": "a meal",
        "stretch": "your muscles",
        "clean": "one space or surface",
        "drink": "some water",
        "reach out to": "someone",
        "remove": "cattle from a stage",
        "raise": "your heartbeat",
        "grab": "a refreshing drink",
        "tend to": "a living/growing thing",
    }.items()
)

BAD_SELF_CARE_TEMPLATES = [
    "{verb} {act_on}?",
    "{verb} {act_on}?",
    "{verb} {act_on}?",
    "In the words of a Cursed little kitty: {verb} {act_on}?",
    "Kitsune says: {verb} {act_on}?",
    "Kitteh says: {verb} {act_on}!",
    "Reminder to: {verb} {act_on}?",
    "Time to {verb} {act_on}?",
]


class BadSelfCare(bot.commands.SimpleCommand):
    """Reminds our dear friends to... oh dear"""

    def __init__(self) -> None:
        super().__init__("badselfcare")

    def message(self) -> str:
        [verb, _], [_, act_on] = random.sample(list(BAD_SELF_CARE_IDEAS), k=2)

        template = random.choice(BAD_SELF_CARE_TEMPLATES)

        return template.format(verb=verb, act_on=act_on).capitalize()
