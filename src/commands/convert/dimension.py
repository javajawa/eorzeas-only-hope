# SPDX-FileCopyrightText: 2025 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations as _future_annotations

from typing import Self

import enum

from .counter import UpDownCounter


class Dimension(enum.Enum):
    MASS = enum.auto()
    LENGTH = enum.auto()
    TIME = enum.auto()
    TEMP = enum.auto()
    CURRENT = enum.auto()
    LUMOSITY = enum.auto()
    AMOUNT = enum.auto()


class Dimensions(UpDownCounter[Dimension]):
    def __bool__(self) -> bool:
        return any(x for x in self.values())

    def __str__(self) -> str:
        strs = [f"[{k}]^{v}" for k, v in self.items() if v]
        if not strs:
            return "[no units]"

        return " ".join(strs)

    def __repr__(self) -> str:
        strs = [f"{k}^{v}" for k, v in self.items() if v]
        if not strs:
            return "Dimensions<{no units}>"

        return f"Dimensions<{{{', '.join(strs)}}}>"


class DimensionComparisonError(ValueError):
    def __init__(self, operation: str, left: Dimensions, right: Dimensions) -> None:
        self.left = left
        self.right = right
        text = f"Can not {operation} {left} to {right}"
        super().__init__(text)


class DimensionedValue:
    _value: int | float
    _dimensions: Dimensions

    def __init__(self, value: float = 1, dimensions: Dimensions | None = None) -> None:
        self._value = value
        self._dimensions = Dimensions(dimensions)

    def __add__(self, other: DimensionedValue) -> DimensionedValue:
        if other._dimensions != self._dimensions:
            raise DimensionComparisonError("add", self._dimensions, other._dimensions)

        return DimensionedValue(self._value + other._value, self._dimensions)

    def __iadd__(self, other: DimensionedValue) -> Self:
        if other._dimensions != self._dimensions:
            raise DimensionComparisonError("add", self._dimensions, other._dimensions)

        self._value += other._value
        return self

    def __sub__(self, other: DimensionedValue) -> DimensionedValue:
        if other._dimensions != self._dimensions:
            raise DimensionComparisonError("add", self._dimensions, other._dimensions)

        return DimensionedValue(self._value - other._value, self._dimensions)

    def __isub__(self, other: DimensionedValue) -> Self:
        if other._dimensions != self._dimensions:
            raise ValueError

        self._value -= other._value
        return self

    def __mul__(self, other: DimensionedValue | float) -> DimensionedValue:
        if not isinstance(other, DimensionedValue):
            return DimensionedValue(self._value * other, self._dimensions)

        return DimensionedValue(
            self._value * other._value,
            Dimensions(self._dimensions + other._dimensions),
        )

    def __imul__(self, other: DimensionedValue | float) -> Self:
        if not isinstance(other, DimensionedValue):
            self._value *= other
            return self

        self._value *= other._value
        self._dimensions += other._dimensions
        return self

    def __pow__(self, power: int, modulo: None = None) -> DimensionedValue:
        return DimensionedValue(self._value**power, Dimensions(self._dimensions * power))

    def __truediv__(self, other: DimensionedValue | float) -> DimensionedValue:
        if not isinstance(other, DimensionedValue):
            return DimensionedValue(self._value / other, self._dimensions)

        return DimensionedValue(
            self._value / other._value,
            Dimensions(self._dimensions - other._dimensions),
        )

    def __itruediv__(self, other: DimensionedValue | float) -> Self:
        if not isinstance(other, DimensionedValue):
            if other != 1:
                self._value /= other
            return self

        if other._value != 1:
            self._value /= other._value
        self._dimensions -= other._dimensions
        return self

    def __str__(self) -> str:
        if isinstance(self._value, int):
            return f"{self._value} {self._dimensions!s}"
        return f"{self._value:.2f} {self._dimensions!s}"

    def __repr__(self) -> str:
        return f"DimensionedValue({self._value}, {self._dimensions})"

    @property
    def value(self) -> int | float:
        return self._value

    @property
    def dimensions(self) -> Dimensions:
        return Dimensions(self._dimensions)
