# SPDX-FileCopyrightText: 2026 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations as _future_annotations

from typing import Self

import math


class VecTwo[T: int | float]:
    x: T
    y: T

    __slots__ = "x", "y"

    def __init__(self, value: tuple[T, T]) -> None:
        self.x, self.y = value

    def __hash__(self) -> int:
        return hash((self.x, self.y))

    def __str__(self) -> str:
        return str((self.x, self.y))

    def __repr__(self) -> str:
        return f"Vec({self.x}, {self.y})"

    def __float__(self) -> float:
        return self % 1

    def __complex__(self) -> complex:
        return complex(self.x, self.y)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VecTwo):
            return NotImplemented

        return self.x == other.x and self.y == other.y  # type: ignore[no-any-return]

    def __mod__(self, other: int) -> float:
        if other != 1:
            return NotImplemented

        return math.sqrt((self.x * self.x) + (self.y * self.y))  # type: ignore[operator]

    def __copy__(self) -> VecTwo[T]:
        return VecTwo((self.x, self.y))

    def __deepcopy__(self, _: object) -> VecTwo[T]:
        return VecTwo((self.x, self.y))

    def __lt__(self, other: object) -> bool:
        if isinstance(other, float | int):
            return float(self) < float(other)

        return NotImplemented

    def __gt__(self, other: object) -> bool:
        if isinstance(other, float | int):
            return float(self) > float(other)

        return NotImplemented

    def copy(self) -> VecTwo[T]:
        return VecTwo((self.x, self.y))

    def dot(self, other: object) -> T:
        if not isinstance(other, VecTwo):
            return NotImplemented  # type: ignore[no-any-return]

        return (self.x * other.x) + (self.y * other.y)  # type: ignore[no-any-return]

    def normalized(self) -> VecTwo[float]:
        magnitude = float(self)
        if magnitude == 0:
            return VecTwo((0.0, 0.0))

        return VecTwo((self.x / magnitude, self.y / magnitude))

    def perpendicular(self) -> VecTwo[T]:
        return VecTwo((-self.y, self.x))  # type: ignore[arg-type]

    def __add__(self, other: object) -> VecTwo[T]:
        if not isinstance(other, VecTwo):
            return NotImplemented

        return VecTwo((self.x + other.x, self.y + other.y))

    def __iadd__(self, other: object) -> Self:
        if not isinstance(other, VecTwo):
            return NotImplemented

        self.x += other.x
        self.y += other.y
        return self

    def __sub__(self, other: object) -> VecTwo[T]:
        if not isinstance(other, VecTwo):
            return NotImplemented

        return VecTwo((self.x - other.x, self.y - other.y))

    def __isub__(self, other: object) -> Self:
        if not isinstance(other, VecTwo):
            return NotImplemented

        self.x -= other.x
        self.y -= other.y
        return self

    def __imul__(self, other: object) -> Self:
        if isinstance(other, float | int):
            self.x *= other  # type: ignore[assignment]
            self.y *= other  # type: ignore[assignment]
            return self

        if isinstance(other, VecTwo):
            self.x *= other.x
            self.y *= other.y
            return self

        return NotImplemented

    def __mul__(self, other: object) -> VecTwo[float | int]:
        if isinstance(other, float | int):
            return VecTwo((self.x * other, self.y * other))
        if isinstance(other, VecTwo):
            return VecTwo((self.x * other.x, self.y * other.y))

        return NotImplemented

    def __itruediv__(self, other: object) -> Self:
        if isinstance(other, float | int):
            self.x /= other  # type: ignore[assignment]
            self.y /= other  # type: ignore[assignment]
            return self

        if isinstance(other, VecTwo):
            self.x /= other.x
            self.y /= other.y
            return self

        return NotImplemented

    def __truediv__(self, other: object) -> VecTwo[float]:
        if isinstance(other, float | int):
            return VecTwo((self.x / other, self.y / other))
        if isinstance(other, VecTwo):
            return VecTwo((self.x / other.x, self.y / other.y))

        return NotImplemented
