#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""Self care commands"""

from __future__ import annotations

from typing import Any, Dict, Generator, List, Union

import itertools
import math
import requests

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

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, DonationAmount):
            return False

        return self.total == other.total and self.coolness == other.coolness

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, DonationAmount):
            return NotImplemented

        return self.value() < other.value()

    def __le__(self, other: Any) -> bool:
        if not isinstance(other, DonationAmount):
            return NotImplemented

        return self.value() <= other.value()

    def __ge__(self, other: Any) -> bool:
        if not isinstance(other, DonationAmount):
            return NotImplemented

        return self.value() >= other.value()

    def __gt__(self, other: Any) -> bool:
        if not isinstance(other, DonationAmount):
            return NotImplemented

        return self.value() > other.value()

    def div(self, rvalue: float, true_current: float) -> DonationAmountFloat:
        return DonationAmountFloat(true_current, self.total / rvalue, self.coolness)

    def __hash__(self) -> int:
        return self.total

    def __str__(self) -> str:
        return f"${(self.total - self.current):,.2f} for ${self.total:,.2f}"


class DonationAmountFloat:
    current: float
    total: float
    coolness: int

    def __init__(self, current: float, total: float, coolness: int) -> None:
        self.current = current
        self.total = total
        self.coolness = coolness if coolness > 0 else 1

    def value(self) -> float:
        amount = self.total - self.current

        if amount < 0:
            return 999999.9

        return amount / self.coolness

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, DonationAmountFloat):
            return False

        return self.total == other.total and self.coolness == other.coolness

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, DonationAmountFloat):
            return NotImplemented

        return self.value() < other.value()

    def __le__(self, other: Any) -> bool:
        if not isinstance(other, DonationAmountFloat):
            return NotImplemented

        return self.value() <= other.value()

    def __ge__(self, other: Any) -> bool:
        if not isinstance(other, DonationAmountFloat):
            return NotImplemented

        return self.value() >= other.value()

    def __gt__(self, other: Any) -> bool:
        if not isinstance(other, DonationAmountFloat):
            return NotImplemented

        return self.value() > other.value()

    def __str__(self) -> str:
        return f"${(self.total - self.current):,.2f} for ${self.total:,.2f}"


AmountGenerator = Generator[DonationAmount, None, None]


def target_round_number(current: int, actual: int) -> AmountGenerator:
    current_str = str(current)

    for pos in range(0, math.ceil(len(current_str) / 2)):
        off = len(current_str) - pos

        target_str = current_str[0:pos] + ("0" * off)
        target = int(target_str)
        target += 10**off

        yield DonationAmount(actual, target, int(1.5 * off))

        target += 10**off

        yield DonationAmount(actual, target, int(1.5 * off))


def target_ascending_number(current: int, actual: int) -> AmountGenerator:
    # current is in pence/cent, to make it an int.

    # This operation is not defined for numbers less than four digits.
    if current < 1000:
        return

    current_str = str(current)
    base = int(current_str[0])
    digits = [x % 10 for x in range(base, base + len(current_str))]
    target = int("".join([str(d) for d in digits]))

    if target > current:
        yield DonationAmount(actual, target, 2 * len(current_str))


def target_descending_number(current: int, actual: int) -> AmountGenerator:
    # current is in pence/cent, to make it an int.

    # This operation is not defined for numbers less than four digits.
    if current < 1000:
        return

    current_str = str(current)
    base = int(current_str[0])
    digits = [x % 10 for x in range(base - len(current_str), base)]
    digits.reverse()
    target = int("".join([str(d) for d in digits]))

    if target > current:
        yield DonationAmount(actual, target, 2 * len(current_str))


def target_repeating_number(current: int, actual: int) -> AmountGenerator:
    current_str = str(current)

    for pos in range(math.ceil(len(current_str) / 2), len(current_str) + 1):
        off = len(current_str) - pos

        target_str = (current_str[0] * pos) + ("0" * off)
        target = int(target_str)

        if target > current:
            cool = max(-1, pos - 3) + max(-1, off - 3)
            yield DonationAmount(actual, target, 2 * cool if off > 0 else 3 * pos)


def target_weed_number(current: int, actual: int) -> AmountGenerator:
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
            target_str = "".join(["69" if x else "420" for x in form])
            target = int(target_str)

            if target > current:
                yield DonationAmount(actual, target, 20)


def target_alternating_number(current: int, actual: int) -> AmountGenerator:
    # current is in pence/cent, to make it an int.

    # This operation is not defined for numbers less than four digits.
    if current < 1000:
        return

    current_str = str(current)
    target_str = current_str[0:2] * math.ceil(len(current_str) / 2)

    target = int(target_str[: len(current_str)])

    if target > current:
        yield DonationAmount(actual, target, 2 * len(current_str) - 1)


def get_targets(min_amount: int, amount: int) -> List[DonationAmount]:
    potential: Dict[int, DonationAmount] = {}

    for target in itertools.chain(
        target_ascending_number(min_amount, amount),
        target_descending_number(min_amount, amount),
        target_alternating_number(min_amount, amount),
        target_round_number(min_amount, amount),
        target_repeating_number(min_amount, amount),
        target_weed_number(min_amount, amount),
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
        print(f"{target.total:8d}  {target.coolness:4d}  {target.value():6,.0f}")
    print()

    return targets


class TeamOrder(bot.commands.ParamCommand):
    def __init__(self) -> None:
        super().__init__("order", 1, 1)

    async def process_args(self, context: bot.commands.MessageContext, *args: str) -> bool:
        targets: Union[List[DonationAmount], List[DonationAmountFloat]]

        if "." in args[0]:
            amount = float(args[0])
            target = get_targets(round(100 * amount), round(100 * amount))
            targets = [x.div(100, amount) for x in target]

        else:
            amount = int(args[0])
            targets = get_targets(amount, amount)

        # Show three at most.
        targets = targets[0:3]
        targets.sort(key=lambda a: a.total)
        output = "Donate " + ", or ".join([str(t) for t in targets[0:3]])

        await context.reply_all(output)

        return True


class TeamOrderDonate(bot.commands.ParamCommand):
    def __init__(self) -> None:
        super().__init__("order_donate", 1, 1)

    async def process_args(self, context: bot.commands.MessageContext, *args: str) -> bool:
        targets: Union[List[DonationAmount], List[DonationAmountFloat]]

        if "." in args[0]:
            amount = float(args[0])
            # Minimum increment is 5 units
            min_amount = amount + 5
            target = get_targets(round(100 * min_amount), round(100 * amount))
            targets = [x.div(100, amount) for x in target]

        else:
            amount = int(args[0])
            # Minimum increment is 1% or 5 units
            min_amount = amount + 5
            targets = get_targets(min_amount, amount)

        # Show three at most.
        targets = targets[0:3]
        targets.sort(key=lambda a: a.total)
        output = "Donate " + ", or ".join([str(t) for t in targets[0:3]])

        await context.reply_all(output)

        return True


class TeamOrderBid(bot.commands.ParamCommand):
    def __init__(self) -> None:
        super().__init__("order_bid", 1, 1)

    async def process_args(self, context: bot.commands.MessageContext, *args: str) -> bool:
        targets: Union[List[DonationAmount], List[DonationAmountFloat]]

        if "." in args[0]:
            amount = float(args[0])
            # Minimum increment is 5 units
            min_amount = max(amount * 1.01, amount + 5)
            target = get_targets(round(100 * min_amount), round(100 * amount))
            targets = [x.div(100, amount) for x in target]

        else:
            amount = int(args[0])
            # Minimum increment is 1% or 5 units
            min_amount = round(min(amount * 1.01, amount + 5))
            targets = get_targets(min_amount, amount)

        # Show three at most.
        targets = targets[0:3]
        targets.sort(key=lambda a: a.total)
        output = "Donate " + ", or ".join([str(t) for t in targets[0:3]])

        await context.reply_all(output)

        return True


class DesertBusOrder(bot.commands.SimpleCommand):
    def __init__(self) -> None:
        super().__init__("busorder")

    def message(self) -> str:
        data = requests.get("https://desertbus.org/wapi/init").json()
        amount = round(100 * data["total"])

        target = get_targets(amount, amount)
        targets = [x.div(100, amount / 100) for x in target]

        # Show three at most.
        targets = targets[0:3]
        targets.sort(key=lambda a: a.total)

        return "Donate " + ", or ".join([str(t) for t in targets])
