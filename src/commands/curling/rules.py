# SPDX-FileCopyrightText: 2026 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations as _future_annotations

import enum

from .vector import VecTwo

# Curling Important Dimensions
# Units are decimeters (1 = 100mm)
CENTER_LINE = 24.0

SIX_FEET = 18.3
LANE_WIDTH = 445.0
LANE_HEIGHT = 48.0

HACK_POINT = LANE_WIDTH - SIX_FEET
BACKLINE = 30.5
TEE_LINE = 48.8
HOG_LINE = 112.8
THROW_LINE = 332.2

STONE_MASS = 19  # in kilograms
STONE_DIAMETER = 2.9  # in decimeters

ASPECT_RATIO = 3.0
FRAMES_PER_SECOND = 24
TIME_STEP = 1 / FRAMES_PER_SECOND

STONE_RADIUS = STONE_DIAMETER / 2
TOTAL_STONES = 8


class Team(enum.IntEnum):
    YELLOW = enum.auto()
    RED = enum.auto()


class Stone:
    colour: Team
    number: int

    position: VecTwo[float]
    velocity: VecTwo[float]
    rotation: float
    spin: float

    def __init__(self, colour: Team, number: int) -> None:
        if number < 1 or number > TOTAL_STONES:
            raise ValueError("Only 8 stones per team")

        self.colour = colour
        self.number = number
        self.position = self.initial_position
        self.velocity = VecTwo((0.0, 0.0))
        self.rotation = 0
        self.spin = 0

    def __hash__(self) -> int:
        return hash((self.colour, self.number))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Stone):
            return self.colour == other.colour and self.number == other.number

        if isinstance(other, tuple):
            return other == (self.colour, self.number)

        return NotImplemented

    def ordering_tuple(self) -> tuple[int, int]:
        return self.number, int(self.colour)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Stone):
            return NotImplemented

        return self.ordering_tuple() < other.ordering_tuple()

    def __str__(self) -> str:
        return f"{self.colour.name.title()} #{self.number}"

    def __repr__(self) -> str:
        return f"Stone<{self.colour.name.title()}#{self.number} at {self.position}>"

    @property
    def initial_position(self) -> VecTwo[float]:
        position = TOTAL_STONES - self.number
        split = int(TOTAL_STONES / 2)

        y_offset = 0.5 + STONE_DIAMETER * (0.5 + (position // split))
        y = y_offset if self.colour == Team.YELLOW else LANE_HEIGHT - y_offset
        x = LANE_WIDTH - STONE_DIAMETER * (0.7 + (position % split))

        return VecTwo((x, y))

    def discard_position(self, position: int) -> VecTwo[float]:
        y_offset = 0.5 + STONE_DIAMETER * ((position % 3) + 0.5)
        y = y_offset if self.colour == Team.YELLOW else LANE_HEIGHT - y_offset
        x = 0.5 + STONE_DIAMETER * (0.5 if position < 3 else 1.5)

        return VecTwo((x, y))

    @property
    def momentum(self) -> float:
        return STONE_MASS * float(self.velocity) / 10

    @property
    def kinetic_energy(self) -> float:
        return STONE_MASS * ((float(self.velocity) / 10) ** 2)
