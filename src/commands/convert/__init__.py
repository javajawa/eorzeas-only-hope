# SPDX-FileCopyrightText: 2025 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations as _future_annotations

import logging

from bot.commands import Command, MessageContext

from .convertor import Convertor
from .dimension import Dimension
from .units import NamedUnit


class ConvertorBot(Command):
    """Convert various units."""

    logger: logging.Logger
    converter: Convertor

    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger
        converter = Convertor(logger)

        # Mass
        converter.add_unit(
            NamedUnit(
                "kilogram",
                {"kg", "kgs", "kilos", "kilograms", "kilogrammes"},
                1,
                Dimension.MASS,
            ),
        )
        converter.add_unit(NamedUnit("gram", {"g", "grams", "grammes"}, 1 / 1000, Dimension.MASS))
        converter.add_unit(NamedUnit("ounce", {"oz", "ozs", "ounces"}, 0.0283495, Dimension.MASS))
        converter.add_unit(NamedUnit("pound", {"lb", "pounds"}, 0.453592, Dimension.MASS))
        converter.add_unit(NamedUnit("stone", {"stones"}, 6.35029, Dimension.MASS))
        converter.add_unit(NamedUnit("short-ton", {"st", "tn"}, 907.18, Dimension.MASS))
        converter.add_unit(NamedUnit("ton", {"tons"}, 1016.0463, Dimension.MASS))
        converter.add_unit(NamedUnit("tonne", {"tonnes"}, 1000, Dimension.MASS))

        # Length
        converter.add_unit(
            NamedUnit("meter", {"m", "metre", "meters", "metres"}, 1, Dimension.LENGTH),
        )
        converter.add_unit(
            NamedUnit("mm", {"mms"}, 1 / 1000, Dimension.LENGTH),
        )
        converter.add_unit(
            NamedUnit("nautical-mile", {"nms", "nm"}, 1852, Dimension.LENGTH),
        )
        converter.add_unit(
            NamedUnit("inch", {"inches", "in"}, 0.0254, Dimension.LENGTH),
        )
        converter.add_unit(
            NamedUnit("foot", {"feet", "ft"}, 0.3048, Dimension.LENGTH),
        )
        converter.add_unit(
            NamedUnit("yard", {"yards", "yd", "yds"}, 0.9144, Dimension.LENGTH),
        )
        converter.add_unit(
            NamedUnit("mile", {"miles", "mi", "mis"}, 1609.34, Dimension.LENGTH),
        )
        converter.add_unit(
            NamedUnit("parsec", {"parsecs"}, 3.086e+16, Dimension.LENGTH),
        )
        converter.add_unit(
            NamedUnit("light second", {"ls", "lightsecond", "lightseconds"}, 2.998e+8, Dimension.LENGTH),
        )
        converter.add_unit(
            NamedUnit("earth radii", {"earthradii", "rearth", "rearths"}, 6378000, Dimension.LENGTH),
        )
        converter.add_unit(
            NamedUnit("pool lengths", {"poollengths"}, 50, Dimension.LENGTH),
        )

        # Area

        # Volume
        converter.add_unit(
            NamedUnit("litre", {"litres", "L", "liters", "liter"}, 1e-3, Dimension.LENGTH, Dimension.LENGTH, Dimension.LENGTH),
        )
        converter.add_unit(
            NamedUnit("cc", {"cubiccentimeters", "ccs"}, 1e-6, Dimension.LENGTH, Dimension.LENGTH, Dimension.LENGTH),
        )
        converter.add_unit(
            NamedUnit("swimming-pools", {"pools", "pool", "swimmingpool", "swimmingpools"}, 2500, Dimension.LENGTH, Dimension.LENGTH, Dimension.LENGTH),
        )

        self.converter = converter

    @property
    def command_hint(self) -> str | None:
        return "!convert [value] [input units] to [output units]"

    @property
    def group(self) -> str | None:
        return "Interactive"

    def matches(self, message: str) -> bool:
        return message.strip().startswith("!convert ") or message.strip() == "!units"

    async def process(self, context: MessageContext, message: str) -> bool:
        """Handle the command in the message"""
        if message.strip() == "!units":
            await context.reply_all(", ".join(self.converter.known_units))
            return True

        try:
            result = self.converter.run(message.removeprefix("!convert").strip())
        except Exception as exc:
            self.logger.exception("bad conversion", exc_info=exc)
            await context.reply_all("Error during conversion: " + str(exc))
        else:
            await context.reply_all(result)
            return True

        return False
