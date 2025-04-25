# SPDX-FileCopyrightText: 2025 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations as _future_annotations

from collections.abc import Iterable, Mapping
from typing import Self, TypeVar

T = TypeVar("T")


class UpDownCounter(dict[T, int]):
    def __init__(self, initial: Iterable[T] | Mapping[T, int] | None = None) -> None:
        super().__init__()

        if isinstance(initial, Mapping):
            for k, v in initial.items():
                self[k] = v
        elif isinstance(initial, Iterable):
            for v in initial:
                self[v] = 1

    def __missing__(self, key: T) -> int:
        """The count of elements not in the Counter is zero."""
        return 0

    def __iadd__(self, other: Mapping[T, int] | T) -> Self:
        if isinstance(other, Mapping):
            for elem, count in other.items():
                self[elem] += count
            return self

        self[other] += 1
        return self

    def __isub__(self, other: Mapping[T, int] | T) -> Self:
        if isinstance(other, Mapping):
            for elem, count in other.items():
                self[elem] -= count
            return self

        self[other] -= 1
        return self

    def __add__(self, other: Mapping[T, int]) -> UpDownCounter[T]:
        if not isinstance(other, Mapping):
            return NotImplemented

        result: UpDownCounter[T] = UpDownCounter()

        for elem, count in self.items():
            result[elem] = count + other[elem]

        for elem, count in other.items():
            if elem not in self:
                result[elem] = count

        return result

    def __sub__(self, other: Mapping[T, int]) -> UpDownCounter[T]:
        if not isinstance(other, Mapping):
            return NotImplemented

        result: UpDownCounter[T] = UpDownCounter()
        for elem, count in self.items():
            result[elem] = count - other[elem]

        for elem, count in other.items():
            if elem not in self:
                result[elem] = -count

        return result

    def __imul__(self, value: int) -> Self:
        if isinstance(value, int):
            for elem, count in self.items():
                self[elem] = count * value
            return self

        raise NotImplementedError
