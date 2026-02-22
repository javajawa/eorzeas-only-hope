# SPDX-FileCopyrightText: 2026 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations as _future_annotations

from bot.commands import Command, MessageContext
from bot.twitch import TwitchMessageContext

CHEER = "KITS"


class CheerCommand(Command):
    state: int | None

    def __init__(self) -> None:
        super().__init__()
        self.state = None

    @property
    def command_hint(self) -> str | None:
        return None

    def matches(self, message: str) -> bool:
        if self.state is None:
            return message == "!cheer"

        return message.upper().rstrip("!? ") == CHEER[self.state]

    async def process(self, context: MessageContext, _: str) -> bool:
        if not isinstance(context, TwitchMessageContext):
            return False

        if str(context.channel()) != "exachixkitsune":
            return False

        self.state = 0 if self.state is None else self.state + 1

        if self.state >= len(CHEER):
            await context.reply_all("Goooooo Kits!!")
            return True

        await context.reply_all("Give me a " + CHEER[self.state])
        return True
