#!/usr/bin/python3
# vim: ts=4 expandtab

"""Bot implementations"""

from __future__ import annotations

from .discord import DiscordBot
from .twitch import TwitchBot


__all__ = ["DiscordBot", "TwitchBot"]
