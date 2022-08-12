#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""Bot implementations"""

from __future__ import annotations

from .discord import DiscordBot
from .twitch import TwitchBot


__all__ = ["DiscordBot", "TwitchBot"]
