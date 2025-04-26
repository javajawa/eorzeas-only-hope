# SPDX-FileCopyrightText: 2025 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations as _future_annotations

from collections.abc import Iterator

import logging
import re

from .dimension import DimensionedValue
from .units import DerivedUnit, NamedUnit, Units

REQUEST_FORMAT_ERROR = (
    "Request must be of the format `[numeric value] [input units] to [output units]`"
)
NUMBER_MATCHER = re.compile(r"^([0-9., ]+)([a-z].*)$")


class DuplicateUnitError(RuntimeError):
    def __init__(self, unit: str) -> None:
        self.unit = unit
        super().__init__(f"Duplicate unit '{unit}'")


class Convertor:
    _logger: logging.Logger
    _known_units: dict[str, NamedUnit]
    _known_aliases: dict[str, NamedUnit]

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._known_units = {}
        self._known_aliases = {}
        self._logger = logger or logging.getLogger(__name__)

    @property
    def known_units(self) -> set[str]:
        return set(self._known_units.keys())

    def add_unit(self, unit: NamedUnit) -> None:
        if unit.name in self._known_aliases:
            raise DuplicateUnitError(unit.name)
        self._known_units[unit.name] = unit
        self._known_aliases[unit.name] = unit
        for alias in unit.aliases:
            if alias in self._known_units:
                raise DuplicateUnitError(alias)
            self._known_aliases[alias] = unit

    def run(self, request: str) -> str:
        if " to " not in request:
            raise ValueError(REQUEST_FORMAT_ERROR)

        left_side, _, o_units = request.partition(" to ")

        if not (match := NUMBER_MATCHER.match(left_side)):
            raise ValueError(REQUEST_FORMAT_ERROR)

        self._logger.info("Handling conversion: ''%s''", request)

        number, i_units = match.groups()

        self._logger.info(
            "Reading message as %s",
            {"value": number, "input_units": i_units, "target units": o_units},
        )

        initial_value = self._parse_value(number)
        input_units = self._parse_units(i_units)
        output_units = self._parse_units(o_units)
        self._logger.info(
            "Reading message as %s",
            {"value": initial_value, "input_units": input_units, "target units": output_units},
        )

        value = DimensionedValue(initial_value)
        value = self._manipulate_units(value, input_units, output_units)

        if value.dimensions:
            # Future Work: look for known constants (like speed of light)
            # That match the dimensions.
            raise ValueError("Input/Output dimensions don't match")

        result = output_units.format(value.value)
        self._logger.info("Converted output: %s", result)

        return result

    def _manipulate_units(
        self,
        value: DimensionedValue,
        input_units: Units,
        output_units: Units,
    ) -> DimensionedValue:
        for unit, (mul, count) in input_units.items():
            value *= unit**count
            value *= 10**mul
        self._logger.info("Fully read input: %s", value)

        for unit, (mul, count) in output_units.items():
            value /= unit**count
            value /= 10**mul
        self._logger.info("Fully handled output: %s", value)

        return value

    def _parse_value(self, number: str) -> int | float:
        number = number.replace("_", "")
        number = number.replace(" ", "")

        dot_count = number.count(".")
        comma_count = number.count(",")

        if dot_count > 1 >= comma_count:
            number = number.replace(".", "").replace(",", ".")
        else:
            number = number.replace(",", "")

        if "." in number:
            return float(number)
        return int(number)

    def _parse_units(self, initial_units: str) -> Units:
        units = initial_units

        # Normalise power values (inc attaching them to the thing before them
        units = re.sub(r" *\^ *-([0-9]+) *", r"ˇ\1 ", units)
        units = re.sub(r" *\^ *([0-9]+) *", r"^\1 ", units)

        # Replace separators with spaces
        units = units.replace("-", " ")
        units = units.replace(".", " ")

        # Reinstate negative powers
        units = re.sub(r" *ˇ *([0-9]+) *", r"^-\1 ", units)

        # Ensure that brackets have spaces inside and out
        units = re.sub(r" *\( *", " ( ", units)
        units = re.sub(r" *\) *", " ) ", units)

        # Normalise divisors to be attached to the word after them
        units = re.sub(" +per +", "/", units)
        units = re.sub("/ +", "/", units)
        units = re.sub(" +/", "/", units)
        units = units.replace("/", " / ")

        units = units.strip()

        divisors = units.count("/")

        if divisors == 0:
            units = "( " + units + " )"
        elif divisors == 1:
            quotient, _, denominator = units.partition(" / ")
            units = "( ( " + quotient + " ) / ( " + denominator + " ) )"
        else:
            raise ValueError("Can't currently handle multiple divisors")

        self._logger.debug("Unit parsing: ''%s'' -> ''%s''", initial_units, units)

        tokens = Tokens(units)

        if next(tokens) != "(":
            raise ValueError("Failed to parse unit")

        return self._parse_unit_tokens(tokens)

    def _parse_unit_tokens(self, tokens: Tokens) -> Units:
        output = Units()
        next_exp_mul = 1

        for tok in tokens:
            if tok == ")":
                return output

            if tok.startswith(")^"):
                tokens.push(tok.strip(")"))
                return output

            if tok == "(":
                self._logger.debug("Starting sub-expression... %s", output)
                sub_value = self._parse_unit_tokens(tokens)

                if tokens.peek().startswith("^"):
                    mul = next(tokens).strip("^")
                    next_exp_mul *= int(mul)

                sub_value *= next_exp_mul
                next_exp_mul = 1

                self._logger.debug("Received sub-expression: %s", sub_value)
                output += sub_value
                self._logger.debug("%s", output)
                continue

            if tok == "/":
                next_exp_mul = -1
                continue

            if "^" in tok:
                unit_name, _exponent = tok.split("^")
                exponent = int(_exponent) * next_exp_mul
            else:
                unit_name = tok
                exponent = next_exp_mul

            unit = self._get_unit(unit_name)
            output.add(unit, exponent)
            self._logger.debug("Adding %s^%d", str(unit), exponent)
            self._logger.debug("(Sub)Expression now %s", output)
            next_exp_mul = 1

        raise ValueError

    def _get_unit(self, unit_name: str) -> NamedUnit | DerivedUnit:
        if unit_name in self._known_aliases:
            return self._known_aliases[unit_name]

        for name, unit in self._known_aliases.items():
            if not unit_name.endswith(name):
                continue

            try:
                return unit.with_si_prefix(unit_name.removesuffix(name))
            except ValueError:
                pass

        err = f"Unknown unit '{unit_name}'"
        raise ValueError(err)


class Tokens(Iterator[str]):
    tokens: list[str]

    def __init__(self, data: str) -> None:
        self.tokens = data.split(" ")
        self.tokens.reverse()

    def __next__(self) -> str:
        if not self.tokens:
            raise StopIteration

        return self.tokens.pop()

    def push(self, token: str) -> None:
        self.tokens.append(token)

    def peek(self) -> str:
        return self.tokens[-1]
