#!/usr/bin/python3
# vim: ts=4 expandtab

"""Self care commands"""

from __future__ import annotations

from typing import Generator, List, Optional, Sequence

import math
import random

import bot.commands


def targetRoundNumber(current: int) -> Generator[int, None, None]:
    currentStr = str(current)

    for pos in range(0, math.ceil(len(currentStr) / 2)):
        off = len(currentStr) - pos

        targetStr = currentStr[0:pos] + ("0" * off)
        target = int(targetStr)
        target += 10 ** off

        yield target


def targetRoundishNumber(current: int) -> Optional[int]:
    currentStr = str(current)
    pos = math.ceil(len(currentStr) / 2)
    off = len(currentStr) - pos

    targetStr = currentStr[0 : pos - 1] + "5" + ("0" * off)
    target = int(targetStr)
    target += 10 ** off

    return target


def targetAscendingNumber(current: int) -> Optional[int]:
    # current is in pence/cent, to make it an int.

    # This operation is not defined for numbers less than four digits.
    if current < 1000:
        return None

    currentStr = str(current)
    base = int(currentStr[0])
    digits = [x % 10 for x in range(base, base + len(currentStr))]
    target = int("".join([str(d) for d in digits]))

    if target < current:
        return None

    return target


def targetDescendingNumber(current: int) -> Optional[int]:
    # current is in pence/cent, to make it an int.

    # This operation is not defined for numbers less than four digits.
    if current < 1000:
        return None

    currentStr = str(current)
    base = int(currentStr[0])
    digits = [x % 10 for x in range(base - len(currentStr), base)]
    digits.reverse()
    target = int("".join([str(d) for d in digits]))

    if target < current:
        return None

    return target


def targetRepeatingNumber(current: int) -> Generator[int, None, None]:
    currentStr = str(current)

    for pos in range(math.ceil(len(currentStr) / 2), len(currentStr)):
        off = len(currentStr) - pos

        targetStr = (currentStr[0] * pos) + ("0" * off)
        target = int(targetStr)

        if target > current:
            yield target


def targetAlternatingNumber(current: int) -> Optional[int]:
    # current is in pence/cent, to make it an int.

    # This operation is not defined for numbers less than four digits.
    if current < 1000:
        return None

    currentStr = str(current)
    targetStr = currentStr[0:2] * math.ceil(len(currentStr) / 2)

    target = int(targetStr[: len(currentStr)])

    if target < current:
        return None

    return target


class TeamOrder(bot.commands.ParamCommand):
    def __init__(self) -> None:
        super().__init__("order", 1, 1)

    async def process_args(
        self, context: bot.commands.MessageContext, *args: str
    ) -> bool:
        if "." in args[0]:
            amount = round(100 * float(args[0]))
            targets = self.get_targets(amount)

            pairs = [((target - amount) / 100, target / 100) for target in targets]
        else:
            amount = int(args[0])
            targets = self.get_targets(amount)

            pairs = [(target - amount, target) for target in targets]

        strs = ["%.2f for %.2f" % x for x in pairs[0:3]]

        await context.reply_all(f"Donate {', or '.join(strs)}")

        return True

    def get_targets(self, amount: int) -> List[int]:
        potential = (
            [
                targetAscendingNumber(amount),
                targetDescendingNumber(amount),
                targetAlternatingNumber(amount),
            ]
            + list(targetRoundNumber(amount))
            + list(targetRepeatingNumber(amount))
        )

        targets = [t for t in potential if t]
        targets = list(dict.fromkeys(targets))
        targets.sort()

        return targets
