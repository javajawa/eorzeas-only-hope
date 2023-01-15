from __future__ import annotations

import re

import bot.commands


MATCHER = re.compile("(^|\\s)(?P<value>-?\\d+(\\.\\d+)?)°? *(?P<unit>[cCFfKrR])(\\s|$|[,;.])")


class TemperatureCommand(bot.commands.Command):
    def __init__(self) -> None:
        pass

    def matches(self, message: str) -> bool:
        return bool(MATCHER.search(message))

    async def process(self, context: bot.commands.MessageContext, message: str) -> bool:
        output = []

        for match in MATCHER.finditer(message):
            try:
                temp = float(match.group("value"))
                unit = match.group("unit").upper()
            except ValueError:
                return False

            conversion = self.convert(temp, unit)
            if conversion:
                output.append(conversion)

        if output:
            await context.reply_all("**Conversions!**: " + "; ".join(output))

        return True

    @staticmethod
    def convert(temp: float, unit: str) -> str:
        if unit == "C":
            fahrenheit = (temp * 9 / 5) + 32
            return f"{temp:.1f}°C is {fahrenheit:.0f}°F"

        if unit == "F":
            celsius = (temp - 32) * 5 / 9
            return f"{temp:.0f}°F is {celsius:.1f}°C"

        if unit == "K":
            celsius = temp - 273.15
            fahrenheit = (celsius * 9 / 5) + 32
            return f"{temp:.0f}K is {celsius:.1f}°C/{fahrenheit:.0f}°F"

        if unit == "R":
            fahrenheit = temp - 459.67
            celsius = (fahrenheit - 32) * 5 / 9
            return f"{temp:.0f}R is {celsius:.1f}°C/{fahrenheit:.0f}°F"

        return ""
