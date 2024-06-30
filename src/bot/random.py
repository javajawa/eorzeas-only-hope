from __future__ import annotations

import abc
import random
import re
from typing import List, Dict

from bot.commands import Command, MessageContext, SimpleCommand, ParamCommand
from bot.twitch import TwitchMessageContext


class RandomCommand(Command):
    _triggers: List[str]
    _replies: List[str]
    _params: Dict[str, List[str]]
    _channels: List[str]

    def __init__(
        self,
        triggers: List[str],
        replies: List[str],
        args: Dict[str, List[str]],
        channels: List[str],
    ) -> None:
        self._triggers = ["!" + trigger.strip("!") for trigger in triggers]
        self._replies = [str(x) for x in replies]
        self._params = {k: [str(x) for x in v] for k, v in args.items()}
        self._channels = channels

    def matches(self, message: str) -> bool:
        return any(
            any(line.startswith(x + " ") or line == x for x in self._triggers)
            for line in message.split("\n")
        )

    async def process(self, context: MessageContext, message: str) -> bool:
        if self._channels:
            if isinstance(context, TwitchMessageContext):
                if str(context.channel()) not in self._channels:
                    return False

        reply_format = random.choice(self._replies)

        if not reply_format:
            return False

        args = {k: random.choice(self._params[k]) for k in self._params}

        reply = reply_format.format(**args)

        await context.reply_all(reply)
        return True


class RegexCommand(RandomCommand, abc.ABC):
    """A "command" that is a reply to a matched regexp"""

    _regexp: re.Pattern  # type: ignore

    def __init__(
        self,
        pattern: str,
        replies: List[str],
        args: Dict[str, List[str]],
        channels: List[str],
    ) -> None:
        super().__init__([], replies, args, channels)
        self._regexp = re.compile(pattern, re.IGNORECASE)

    def matches(self, message: str) -> bool:
        """Check if this command is matched"""

        return self._regexp.search(message) is not None


class HelpCommand(Command):
    help: list[str]

    def __init__(self, commands: list[Command]) -> None:
        self.help = []

        for command in commands:
            if isinstance(command, SimpleCommand):
                self.help.append(command._command)
            if isinstance(command, RandomCommand):
                self.help.append(" / ".join(command._triggers))
            if isinstance(command, ParamCommand):
                self.help.append(command._command)

        self.help = [x for x in self.help if x]

    def matches(self, message: str) -> bool:
        return message == "!help"

    async def process(self, context: MessageContext, message: str) -> bool:
        await context.reply_direct("Commands:\n- " + "\n- ".join(self.help))
        return True
