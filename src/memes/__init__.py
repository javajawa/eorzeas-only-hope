#!/usr/bin/python3
# vim: ts=4 expandtab

"""Self care commands"""

from __future__ import annotations

from typing import Any, Dict, Generator, List, Union

import itertools
import math

import bot.commands


Number = Union[float, int]


class DonationAmount:
    current: int
    total: int
    coolness: int

    def __init__(self, current: int, total: int, coolness: int) -> None:
        self.current = current
        self.total = total
        self.coolness = coolness if coolness > 0 else 1

    def value(self) -> float:
        amount = self.total - self.current

        if amount < 0:
            return 999999.9

        return amount / self.coolness

    def __eq__(self, other: Any) -> Union[bool, type(NotImplemented)]:
        if not isinstance(other, DonationAmount):
            return NotImplemented

        return self.total == other.total and self.coolness == other.coolness

    def __lt__(self, other: Any) -> Union[bool, type(NotImplemented)]:
        if not isinstance(other, DonationAmount):
            return NotImplemented

        return self.value() < other.value()

    def __le__(self, other: Any) -> Union[bool, type(NotImplemented)]:
        if not isinstance(other, DonationAmount):
            return NotImplemented

        return self.value() <= other.value()

    def __ge__(self, other: Any) -> Union[bool, type(NotImplemented)]:
        if not isinstance(other, DonationAmount):
            return NotImplemented

        return self.value() >= other.value()

    def __gt__(self, other: Any) -> Union[bool, type(NotImplemented)]:
        if not isinstance(other, DonationAmount):
            return NotImplemented

        return self.value() > other.value()

    def div(self, rvalue: float, true_current: float) -> DonationAmountFloat:
        return DonationAmountFloat(true_current, self.total / rvalue, self.coolness)

    def __hash__(self) -> int:
        return self.total

    def __str__(self) -> str:
        return f"${(self.total - self.current):.2f} for ${self.total:.2f}"


class DonationAmountFloat:
    current: float
    total: float
    coolness: int

    def __init__(self, current: float, total: float, coolness: int) -> None:
        self.current = current
        self.total = total
        self.coolness = coolness if coolness > 0 else 1

    def __str__(self) -> str:
        return f"${(self.total - self.current):.2f} for ${self.total:.2f}"


AmountGenerator = Generator[DonationAmount, None, None]


def targetRoundNumber(current: int) -> AmountGenerator:
    currentStr = str(current)

    for pos in range(0, math.ceil(len(currentStr) / 2)):
        off = len(currentStr) - pos

        targetStr = currentStr[0:pos] + ("0" * off)
        target = int(targetStr)
        target += 10 ** off

        yield DonationAmount(current, target, int(1.5 * off))

        target += 10 ** off

        yield DonationAmount(current, target, int(1.5 * off))


def targetAscendingNumber(current: int) -> AmountGenerator:
    # current is in pence/cent, to make it an int.

    # This operation is not defined for numbers less than four digits.
    if current < 1000:
        return None

    currentStr = str(current)
    base = int(currentStr[0])
    digits = [x % 10 for x in range(base, base + len(currentStr))]
    target = int("".join([str(d) for d in digits]))

    if target > current:
        yield DonationAmount(current, target, 2 * len(currentStr))


def targetDescendingNumber(current: int) -> AmountGenerator:
    # current is in pence/cent, to make it an int.

    # This operation is not defined for numbers less than four digits.
    if current < 1000:
        return None

    currentStr = str(current)
    base = int(currentStr[0])
    digits = [x % 10 for x in range(base - len(currentStr), base)]
    digits.reverse()
    target = int("".join([str(d) for d in digits]))

    if target > current:
        yield DonationAmount(current, target, 2 * len(currentStr))


def targetRepeatingNumber(current: int) -> AmountGenerator:
    currentStr = str(current)

    for pos in range(math.ceil(len(currentStr) / 2), len(currentStr) + 1):
        off = len(currentStr) - pos

        targetStr = (currentStr[0] * pos) + ("0" * off)
        target = int(targetStr)

        if target > current:
            cool = max(-1, pos - 3) + max(-1, off - 3)
            yield DonationAmount(current, target, 2 * cool if off > 0 else 3 * pos)


def targetWeedNumber(current: int) -> AmountGenerator:
    length = len(str(current))

    for sixty_nine_count in range(0, 1 + math.ceil(length / 2)):
        space_left = length - 2 * sixty_nine_count

        if space_left < 0:
            break

        four_twenty_count = math.ceil(space_left / 3)

        space_left -= four_twenty_count * 3

        if space_left < 0:
            continue

        inputs = ([0] * four_twenty_count) + ([1] * sixty_nine_count)

        for form in set(itertools.permutations(inputs, len(inputs))):
            targetStr = "".join(["69" if x else "420" for x in form])
            target = int(targetStr)

            if target > current:
                yield DonationAmount(current, target, 20)


def targetAlternatingNumber(current: int) -> AmountGenerator:
    # current is in pence/cent, to make it an int.

    # This operation is not defined for numbers less than four digits.
    if current < 1000:
        return None

    currentStr = str(current)
    targetStr = currentStr[0:2] * math.ceil(len(currentStr) / 2)

    target = int(targetStr[: len(currentStr)])

    if target > current:
        yield DonationAmount(current, target, 2 * len(currentStr) - 1)


class TeamOrder(bot.commands.ParamCommand):
    def __init__(self) -> None:
        super().__init__("order", 1, 1)

    async def process_args(
        self, context: bot.commands.MessageContext, *args: str
    ) -> bool:
        targets: Union[List[DonationAmount], List[DonationAmountFloat]]

        if "." in args[0]:
            amount = float(args[0])
            target = self.get_targets(round(100 * amount))
            targets = [x.div(100, amount) for x in target]

        else:
            amount = int(args[0])
            targets = self.get_targets(amount)

        # Show three at most.
        targets = targets[0:3]
        targets.sort(key=lambda a: a.total)
        output = "Donate " + ", or ".join([str(t) for t in targets[0:3]])

        await context.reply_all(output)

        return True

    def get_targets(self, amount: int) -> List[DonationAmount]:
        potential: Dict[int, DonationAmount] = {}

        for target in itertools.chain(
            targetAscendingNumber(amount),
            targetDescendingNumber(amount),
            targetAlternatingNumber(amount),
            targetRoundNumber(amount),
            targetRepeatingNumber(amount),
            targetWeedNumber(amount),
        ):

            if target.total in potential:
                potential[target.total].coolness = max(
                    potential[target.total].coolness, target.coolness
                )
            else:
                potential[target.total] = target

        targets = list(potential.values())
        targets.sort()

        print(f"Preview for {amount}")
        for target in targets:
            print(f"{target.total:8d}  {target.coolness:4d}  {target.value():6.0f}")
        print()

        return targets
