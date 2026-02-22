# SPDX-FileCopyrightText: 2025 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations as _future_annotations

import logging

from bot.commands import Command, MessageContext

from .convertor import Convertor
from .dimension import Dimension, Dimensions
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
            NamedUnit("parsec", {"parsecs"}, 3.086e16, Dimension.LENGTH),
        )
        converter.add_unit(
            NamedUnit(
                "light second",
                {"ls", "lightsecond", "lightseconds"},
                2.998e8,
                Dimension.LENGTH,
            ),
        )
        converter.add_unit(
            NamedUnit(
                "earth radii",
                {"earthradii", "rearth", "rearths", "r_earth"},
                6378000,
                Dimension.LENGTH,
            ),
        )
        converter.add_unit(
            NamedUnit("pool lengths", {"poollength s"}, 50, Dimension.LENGTH),
        )
        converter.add_unit(
            NamedUnit("Cara", {"moogle", "cara", "Cara's", "Caras"}, 1.575, Dimension.LENGTH),
        )

        # Area
        converter.add_unit(
            NamedUnit("acre", {"acres"}, 4046.856, Dimension.LENGTH, Dimension.LENGTH),
        )
        converter.add_unit(
            NamedUnit("hectare", {"hectares"}, 10000, Dimension.LENGTH, Dimension.LENGTH),
        )
        converter.add_unit(
            NamedUnit("barn", {"barns"}, 1e-28, Dimension.LENGTH, Dimension.LENGTH),
        )

        # Volume
        converter.add_unit(
            NamedUnit(
                "litre",
                {"litres", "L", "liters", "liter"},
                1e-3,
                Dimension.LENGTH,
                Dimension.LENGTH,
                Dimension.LENGTH,
            ),
        )
        converter.add_unit(
            NamedUnit(
                "pint",
                {"pints"},
                0.000568261,
                Dimension.LENGTH,
                Dimension.LENGTH,
                Dimension.LENGTH,
            ),
        )
        converter.add_unit(
            NamedUnit(
                "pint[us]",
                set(),
                0.000473176,
                Dimension.LENGTH,
                Dimension.LENGTH,
                Dimension.LENGTH,
            ),
        )
        converter.add_unit(
            NamedUnit(
                "cc",
                {"cubiccentimeters", "ccs"},
                1e-6,
                Dimension.LENGTH,
                Dimension.LENGTH,
                Dimension.LENGTH,
            ),
        )
        converter.add_unit(
            NamedUnit(
                "swimming-pools",
                {"pools", "pool", "swimmingpool", "swimmingpools"},
                2500,
                Dimension.LENGTH,
                Dimension.LENGTH,
                Dimension.LENGTH,
            ),
        )

        # Time
        converter.add_unit(NamedUnit("second", {"seconds", "s", "sec"}, 1, Dimension.TIME))
        converter.add_unit(NamedUnit("minute", {"min", "mins", "minutes"}, 60, Dimension.TIME))
        converter.add_unit(NamedUnit("hour", {"hours", "hr", "hrs"}, 3600, Dimension.TIME))
        converter.add_unit(NamedUnit("day", {"days"}, 86400, Dimension.TIME))
        converter.add_unit(NamedUnit("month", {"months"}, 2360591.5, Dimension.TIME))
        converter.add_unit(NamedUnit("year", {"years"}, 31536000, Dimension.TIME))
        converter.add_unit(
            NamedUnit(
                "sidereal year",
                {"siderealyear", "siderealyears"},
                31558149.76,
                Dimension.TIME,
            ),
        )

        # Speed
        converter.add_unit(
            NamedUnit("mph", set(), 0.44704, dims={Dimension.LENGTH: 1, Dimension.TIME: -1}),
        )
        converter.add_unit(
            NamedUnit("knots", set(), 0.51444, dims={Dimension.LENGTH: 1, Dimension.TIME: -1}),
        )

        # Energy / Power
        converter.add_unit(
            NamedUnit(
                "joule",
                {"J", "Joules", "Joule", "joules"},
                1,
                dims={Dimension.MASS: 1, Dimension.LENGTH: 2, Dimension.TIME: -2},
            ),
        )
        converter.add_unit(
            NamedUnit(
                "watt",
                {"W", "watts", "Watt", "Watts"},
                1,
                dims={Dimension.MASS: 1, Dimension.LENGTH: 2, Dimension.TIME: -3},
            ),
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
            return await self.display_units(context)

        try:
            result = self.converter.run(message.removeprefix("!convert").strip())
        except Exception as exc:
            self.logger.exception("bad conversion", exc_info=exc)
            await context.reply_all("Error during conversion: " + str(exc))
        else:
            await context.reply_all(result)
            return True

        return False

    async def display_units(self, context: MessageContext) -> bool:
        other = Dimensions()
        groupings: dict[Dimensions, tuple[str, list[NamedUnit]]] = {
            Dimensions({Dimension.LENGTH: 1}): ("Length", []),
            Dimensions({Dimension.LENGTH: 2}): ("Area", []),
            Dimensions({Dimension.LENGTH: 3}): ("Volume", []),
            Dimensions({Dimension.MASS: 1}): ("Mass", []),
            Dimensions({Dimension.TIME: 1}): ("Time", []),
            Dimensions({Dimension.LENGTH: 1, Dimension.TIME: -1}): ("Speed", []),
            other: ("Other", []),
        }

        for unit in self.converter.known_units:
            if unit.dimensions in groupings:
                groupings[unit.dimensions][1].append(unit)
            else:
                groupings[other][1].append(unit)

        message = "\n".join(
            f"**{k}**: {", ".join(u.name for u in v)}" for k, v in groupings.values()
        )
        await context.reply_all(message)
        return True
