from __future__ import annotations

from typing import TypedDict

import re

import aiohttp

import bot.commands


TEMP_MATCHER = re.compile(
    "(^|\\s)(?P<value>-?\\d+(\\.\\d+)?)°? *(?P<unit>[cCFfKrR])(\\s|$|[,;.])"
)
LATLON_PATTERN = re.compile(r"^[+-]?[0-9]+(\.[0-9]+)?\s*°?[NnEeSsWw]?$")


class TemperatureCommand(bot.commands.Command):
    def __init__(self) -> None:
        pass

    def matches(self, message: str) -> bool:
        return bool(TEMP_MATCHER.search(message))

    async def process(self, context: bot.commands.MessageContext, message: str) -> bool:
        output = []

        for match in TEMP_MATCHER.finditer(message):
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


class Geocoding(TypedDict):
    name: str
    local_names: dict[str, str]
    lat: float
    lon: float
    country: str
    state: str


class Weather(bot.commands.ParamCommand):
    key: str
    geo_cache: dict[str, list[Geocoding]]

    def __init__(self, key: str) -> None:
        super().__init__("weather", 1, 8)
        self.key = key
        self.geo_cache = {}

    async def process_args(self, context: bot.commands.MessageContext, *args: str) -> bool:
        async with aiohttp.client.ClientSession() as session:
            location = self.extract_lat_lon(args)
            message = ""

            if not location:
                query = " ".join(args)
                location_data = await self.do_geo_location(session, query)

                if not location_data:
                    await context.reply_all(f"Unable to get a location for '{query}'")
                    return False

                message = (
                    f"Geocoded to {location_data['local_names'].get('en', location_data['name'])}, "
                    f"{location_data['state']}, {location_data['country']}\n"
                )

                location = location_data["lat"], location_data["lon"]

            message += await self.get_message(session, *location)

        await context.reply_all(message)
        return True

    @staticmethod
    def extract_lat_lon(args: tuple[str, ...]) -> tuple[float, float] | None:
        if len(args) != 2:
            return None

        if not LATLON_PATTERN.match(args[0]):
            return None

        if not LATLON_PATTERN.match(args[1]):
            return None

        if args[0][-1] in "eEwW":
            args = (args[1], args[0])

        lat = args[0].strip("°NnEeSsWw").strip()
        lon = args[1].strip("°NnEeSsWw").strip()

        return float(lat), float(lon)

    async def do_geo_location(
        self, session: aiohttp.ClientSession, query: str
    ) -> Geocoding | None:
        if query in self.geo_cache:
            return next(iter(self.geo_cache.get(query, [])), None)

        geo = await session.get(
            "https://api.openweathermap.org/geo/1.0/direct",
            params={"q": query, "limit": "10", "appid": self.key},
        )
        data = await geo.json()

        self.geo_cache[query] = data

        return next(iter(data), None)

    async def get_message(
        self, session: aiohttp.ClientSession, lat: float, lon: float
    ) -> str:
        geo = await session.get(
            "https://api.openweathermap.org/data/2.5/onecall",
            params={"lat": lat, "lon": lon, "appid": self.key},
        )
        data = await geo.json()

        max_temp = max(data["hourly"][:20], key=lambda x: float(x["feels_like"]))
        min_temp = min(data["hourly"][:20], key=lambda x: float(x["feels_like"]))

        response = (
            f"Weather at "
            f"{abs(data['lat']):.1f}°{'N' if data['lat'] >= 0 else 'S'} "
            f"{abs(data['lon']):.1f}°{'E' if data['lon'] >= 0 else 'W'} "
            f"(timezone {data['timezone_offset']//3600:+03d}{data['timezone_offset']%3600//60:02d})"
            "\n"
            f"Currently {self.temp_str(data['current'])}\n"
            f"Low at <t:{min_temp['dt']}> {self.temp_str(min_temp)}\n"
            f"High at <t:{max_temp['dt']}> {self.temp_str(max_temp)}\n"
        )

        return response

    @staticmethod
    def temp(kelvins: float) -> str:
        celsius = kelvins - 273.15
        fahrenheit = (celsius * 9 / 5) + 32
        return f"{celsius:.1f}°C/{fahrenheit:.0f}°F"

    def temp_str(self, data: dict[str, str | float | list[dict[str, str]]]) -> str:
        return (
            f"{data['weather'][0]['description']} {self.temp(data['temp'])} "  # type: ignore
            f"(feels like {self.temp(data['feels_like'])} at "
            f"{data['humidity']}%RH and {data['pressure']}mBar)"
        )
