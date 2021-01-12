#!/usr/bin/env python3
# vim: ts=4 expandtab

"""Self care commands"""

from __future__ import annotations

import requests

import prosegen

import bot.commands


class Sergeism(bot.commands.SimpleCommand):
    """Become Serge."""

    prosegen: prosegen.ProseGen

    def __init__(self) -> None:
        super().__init__("sergeism", self.message)

        data = requests.get(
            "https://raw.githubusercontent.com/RebelliousUno/BrewCrewQuoteDB/main/quotes.txt"
        )
        self.prosegen = prosegen.ProseGen(8)

        for line in data.text.split("\n"):
            line = line.strip()

            if not line:
                continue

            quotes = line.split('"')[1::2]

            for quote in quotes:
                self.prosegen.add_knowledge(quote)

    def message(self) -> str:
        for _ in range(0, 100):
            wisdom = self.prosegen.make_statement()

            if 16 < len(wisdom) < 60:
                return wisdom

        return "I love coffee!"
