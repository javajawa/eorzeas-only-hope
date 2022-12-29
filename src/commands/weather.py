from __future__ import annotations

import re

import bot.commands


MATCHER = re.compile("(?P<value>-?\\d+(\\.\\d+)?)°? *(?P<unit>[cCFfkKrR])(\\s|$|[,;.])")


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

            if unit == "C":
                fahrenheit = (temp * 9/5) + 32
                output.append(f"{temp:.1f}°C is {fahrenheit:.0f}°F")
            elif unit == "F":
                celsius = (temp - 32) * 5 / 9
                output.append(f"{temp:.0f}°F is {celsius:.1f}°C")
            elif unit == "K":
                celsius = (temp - 273.15)
                fahrenheit = (celsius * 9 / 5) + 32
                output.append(f"{temp:.0f}K is {celsius:.1f}°C/{fahrenheit:.0f}°F")
            elif unit == "R":
                fahrenheit = (temp - 459.67)
                celsius = (fahrenheit - 32) * 5 / 9
                output.append(f"{temp:.0f}R is {celsius:.1f}°C/{fahrenheit:.0f}°F")

        if output:
            await context.reply_all("**Conversions!**: " + "; ".join(output))

        return True
