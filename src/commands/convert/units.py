# SPDX-FileCopyrightText: 2025 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations as _future_annotations

from typing import NamedTuple, Self

import io

from .dimension import Dimension, DimensionedValue, Dimensions

_SI_PREFIXES: dict[str, int] = {
    "tera": 12,
    "giga": 9,
    "mega": 6,
    "kilo": 3,
    "deka": 1,
    "deci": -1,
    "centi": -2,
    "milli": -3,
    "micro": -6,
    "nano": -9,
    "pico": -12,
}


class NamedUnit(DimensionedValue):
    name: str
    aliases: frozenset[str]

    def __init__(self, name: str, aliases: set[str], value: int | float, *dimensions: Dimension) -> None:
        super().__init__(value, Dimensions(dimensions))
        self.name = name
        self.aliases = frozenset(aliases)

    def with_si_prefix(self, prefix: str) -> DerivedUnit:
        if prefix in _SI_PREFIXES:
            return DerivedUnit(_SI_PREFIXES[prefix], self)

        raise ValueError

    def __iadd__(self, other: DimensionedValue | float) -> Self:
        return NotImplemented

    def __isub__(self, other: DimensionedValue | float) -> Self:
        return NotImplemented

    def __imul__(self, other: DimensionedValue | float) -> Self:
        return NotImplemented

    def __itruediv__(self, other: DimensionedValue | int | float) -> Self:
        return NotImplemented

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"Unit<{self.name} {{{self._dimensions}}}>"


class DerivedUnit:
    prefix: int
    unit: NamedUnit

    def __init__(self, prefix: int, unit: NamedUnit) -> None:
        self.prefix = prefix
        self.unit = unit

    def __str__(self) -> str:
        return f"{_si_to_name(self.prefix)}{self.unit.name}"


class _UnitFactor(NamedTuple):
    prefix: int
    exponent: int


class Units(dict[NamedUnit, _UnitFactor]):
    def __missing__(self, name: NamedUnit) -> _UnitFactor:
        return _UnitFactor(0, 0)

    def __iadd__(self, other: Units | NamedUnit | DerivedUnit) -> Self:
        if isinstance(other, NamedUnit | DerivedUnit):
            return self.add(other, 1)

        if not isinstance(other, Units):
            return NotImplemented

        for k, v in other.items():
            cur = self[k]
            self[k] = _UnitFactor(cur.prefix + v.prefix, cur.exponent + v.exponent)
        return self

    def __isub__(self, other: Units | NamedUnit | DerivedUnit) -> Self:
        if isinstance(other, NamedUnit | DerivedUnit):
            return self.add(other, -1)

        if not isinstance(other, Units):
            return NotImplemented

        for k, v in other.items():
            cur = self[k]
            self[k] = _UnitFactor(cur.prefix - v.prefix, cur.exponent - v.exponent)
        return self

    def __imul__(self, other: int) -> Self:
        for unit, cur in self.items():
            self[unit] = _UnitFactor(other * cur.prefix, other * cur.exponent)

        return self

    def add(self, unit: NamedUnit | DerivedUnit, exponent: int) -> Self:
        if isinstance(unit, NamedUnit):
            cur = self[unit]
            self[unit] = _UnitFactor(cur.prefix, cur.exponent + exponent)
            return self

        if isinstance(unit, DerivedUnit):
            cur = self[unit.unit]
            self[unit.unit] = _UnitFactor(
                cur.prefix + (unit.prefix * exponent),
                cur.exponent + exponent,
            )
            return self

        raise NotImplementedError

    def format(self, value: float) -> str:
        sorts: dict[NamedUnit, _UnitFactor] = dict(
            sorted(
                sorted(self.items(), key=lambda i: i[1].prefix / i[1].exponent),
                key=lambda i: i[1].exponent,
                reverse=True,
            ),
        )

        with io.StringIO() as buffer:
            if isinstance(value, int):
                buffer.write(f"{value:,d}")
            else:
                buffer.write(f"{value:,.3f}")
            buffer.write(" ")

            last_positive: bool | None = None

            for unit, (prefix, exponent) in sorts.items():
                if not exponent:
                    continue

                if last_positive and exponent < 0:
                    buffer.write("per-")

                si = prefix // exponent
                buffer.write(_si_to_name(si))
                buffer.write(unit.name)
                if exponent > 0:
                    buffer.write("s")
                if exponent > 1 or exponent < -1:
                    buffer.write("^")
                    buffer.write(str(exponent))
                buffer.write("-")

                last_positive = exponent > 0

            return buffer.getvalue().strip("-")


def _si_to_name(si: int) -> str:
    if not si:
        return ""

    for name, exp in _SI_PREFIXES.items():
        if exp == si:
            return name

    return f"(E{si})"
