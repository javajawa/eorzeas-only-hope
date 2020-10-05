#!/usr/bin/python3
# vim: ts=4 expandtab

"""Self care commands"""

from __future__ import annotations

import requests

import bot.commands


class Cat(bot.commands.SimpleCommand):
    """Reminds our dear friends to look after themselves."""

    def __init__(self) -> None:
        super().__init__("cat", Cat.message)

    @staticmethod
    def message() -> str:
        data = requests.get(url="https://api.thecatapi.com/v1/images/search").json()

        return str(data[0]["url"]) if data else ""
