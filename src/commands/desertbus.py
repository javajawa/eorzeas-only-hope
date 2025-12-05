# SPDX-FileCopyrightText: 2025 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations as _future_annotations

import asyncio
import collections
import concurrent.futures
import csv
import dataclasses
import datetime
import io
import math
import time

import aiohttp

import bot.commands
from bot.commands import MessageContext
from commands.order import get_targets

MOONBASE_TIME = datetime.timezone(-datetime.timedelta(hours=8), "Canada/Pacific")
MARCH_START = datetime.datetime(2020, 3, 1, 0, tzinfo=MOONBASE_TIME)
BUS_START = datetime.datetime(2026, 11, 14, 15, tzinfo=MOONBASE_TIME)
SHIFT_START = datetime.datetime(2026, 11, 14, 12, tzinfo=MOONBASE_TIME)
OMEGA_START = datetime.datetime(2026, 11, 21, 10, tzinfo=MOONBASE_TIME)
BUS_END = datetime.datetime(2026, 11, 21, 14, tzinfo=MOONBASE_TIME)

WEEKDAYS: list[str] = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

SUFFIX: list[str] = ["th", "st", "nd", "rd"]
SHIFTS: list[str] = ["Alpha Flight", "Night Watch", "Zeta", "Dawn Guard", "Omega"]

EXPANSIONS: list[str] = [
    "",  # 0 offset, and there is no day 0
    "Departure",
    "New Bussing Back",
    "The Open Road",
    "(Barely) Living Legends",
    "A Bus Forward",
    "(Guest) Callings",
    "The Heart of a Chat",
    "End of Days (Permatwilight)",
]

DB_DONATION_PUBSUB = (
    "https://pubsub.pubnub.com/history/"
    "sub-cbd7f5f5-1d3f-11e2-ac11-877a976e347c/total:GDVQRLBPQMSG/0/1"
)


class BusIsComing(bot.commands.SimpleCommand):
    """Count down to Desert Bus (in Desert Bus Points"""

    def __init__(self) -> None:
        super().__init__("bus")

    @property
    def group(self) -> str:
        return "Desert Bus"

    async def message(self) -> str:
        now: datetime.datetime = datetime.datetime.now(MOONBASE_TIME)

        if now < BUS_START:
            return pre_bus_message(now)

        if now > BUS_END:
            return post_bus_message()

        if now > OMEGA_START:
            return omega_message(now)

        diff: datetime.timedelta = now - SHIFT_START
        times: int

        shift = diff.seconds // (6 * 3600)
        times = diff.seconds - shift * 6 * 3600

        date: int = diff.days

        shift_name = SHIFTS[shift % 4]
        time_str = f"{times // 3600}:{(times // 60 % 60):02}:{(times % 60):02}"

        total_shift = 4 * date + shift + 1
        suffix: str = (
            SUFFIX[total_shift % 10]
            if total_shift % 10 < len(SUFFIX) and not (10 < total_shift < 13)
            else "th"
        )

        return f"It is {time_str} on {shift_name}, the {total_shift}{suffix} of Bus"


def post_bus_message() -> str:
    return (
        "Typical! You wait all year for a bus, "
        "and five shifts come along at once. "
        "Whelp, have to wait until next year now."
    )


def pre_bus_message(now: datetime.datetime) -> str:
    points: float = (BUS_START - now).total_seconds() / (8 * 3600 + 2 * 60)
    s_points: str = f"{points:.1f}" if points > 1 else f"{points:.2f}"
    return f"Bus Is Coming. Auto-James must acquire {s_points} more points to summon The Bus."


def omega_message(now: datetime.datetime) -> str:
    omega_diff: datetime.timedelta = now - OMEGA_START
    times = omega_diff.seconds
    omega_hours: float = times // 3600
    omega_minutes: float = times // 60 % 60
    omega_seconds: float = times % 60
    return (
        f"We are {omega_hours}:{omega_minutes:02}:{omega_seconds:02} "
        "into Omega, may the Bus protect us!"
    )


class BusStop(bot.commands.SimpleCommand):
    def __init__(self, session: aiohttp.ClientSession) -> None:
        super().__init__("busstop")
        self.session = session

    @property
    def group(self) -> str:
        return "Desert Bus"

    @staticmethod
    def hours(amount: float) -> float:
        return math.log(amount + 14.2857, 1.07) - math.log(15.2857, 1.07) + 1

    async def message(self) -> str:
        request = await self.session.get(DB_DONATION_PUBSUB)
        data = await request.json(content_type="text/javascript")
        amount = data[0]
        hours = BusStop.hours(amount)

        end = time.mktime(BUS_START.utctimetuple())
        end += round(3600 * hours)
        end = int(end)

        return f"The next bus stop on the time table is <t:{end}:R>!"


class DesertBusOrder(bot.commands.SimpleCommand):
    session: aiohttp.ClientSession

    def __init__(self, session: aiohttp.ClientSession) -> None:
        super().__init__("busorder")
        self.session = session

    @property
    def group(self) -> str:
        return "Desert Bus"

    async def message(self) -> str:
        request = await self.session.get(DB_DONATION_PUBSUB)
        data = await request.json(content_type="text/javascript")
        amount = data[0]
        amount = round(100 * amount)

        target = get_targets(amount, amount)
        targets = [x.div(100, amount / 100) for x in target]

        # Show three at most.
        targets = targets[0:3]
        targets.sort(key=lambda a: a.total)

        return "Donate " + ", or ".join([str(t) for t in targets])


class DesertBus(int):
    __slots__ = ()

    @property
    def name(self) -> str:
        if self > 10:
            return "DB" + str(self + 2006)
        if self > 0:
            return "DB" + str(self)

        if self == 0:
            return "RPBS"
        return "DBEX" + str(-self)

    @property
    def vst_site(self) -> str:
        if self > 0:
            return "DB" + str(self)

        if self == 0:
            return "extras/RPBS"

        return "extras/DBEX" + str(-self)

    @property
    def ident(self) -> str:
        return "__" + str(self) + "__"


@dataclasses.dataclass(frozen=True, slots=True)
class DBEvent:
    event_meta_id: DesertBus
    event_day_id: int
    event_line_id: int

    time: str
    title: str
    link: str | None

    def __str__(self) -> str:
        prefix = f"[{self.event_meta_id.name} {self.time}](<{self.sheet_link}>)"
        if self.link:
            return f"{prefix} [{self.title}](<{self.link}>)"
        return f"{prefix} {self.title}"

    @property
    def event_name(self) -> str:
        if self.event_meta_id > 10:
            return "DB" + str(self.event_meta_id + 2006)
        return "DB" + str(self.event_meta_id)

    @property
    def sheet_link(self) -> str:
        return (
            f"https://vst.ninja/DB{self.event_meta_id.vst_site}/index.php"
            f"?day={self.event_day_id}&cell=spareadsheet_line"
            f"#D{self.event_day_id}L{self.event_line_id}"
        )

    @property
    def _tuple(self) -> tuple[int, int, int]:
        return self.event_meta_id, self.event_day_id, self.event_line_id

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DBEvent):
            return NotImplemented
        return self._tuple == other._tuple

    def __hash__(self) -> int:
        return hash(self._tuple)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, DBEvent):
            return NotImplemented

        return self._tuple < other._tuple

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, DBEvent):
            return NotImplemented

        return self._tuple > other._tuple

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, DBEvent):
            return NotImplemented

        return self._tuple >= other._tuple

    def __le__(self, other: DBEvent) -> bool:
        if not isinstance(other, DBEvent):
            return NotImplemented

        return self._tuple <= other._tuple


class VSTSearch(bot.commands.Command):
    _loop: asyncio.AbstractEventLoop
    _session: aiohttp.ClientSession
    _executor: concurrent.futures.ThreadPoolExecutor
    _load_task: asyncio.Task[None]

    _events: dict[str, set[DBEvent]]

    def __init__(self, loop: asyncio.AbstractEventLoop, session: aiohttp.ClientSession) -> None:
        super().__init__()

        self._loop = loop
        self._session = session
        self._executor = concurrent.futures.ThreadPoolExecutor(4, "vst-fetch")

        self._events = collections.defaultdict(set)
        self._load_task = self._loop.create_task(self._load_data())

    @property
    def command_hint(self) -> str | None:
        return "!vst [db00] [search terms]"

    async def _load_data(self) -> None:
        for year in range(-1, 20):
            await self._load_year(DesertBus(year))

    async def _load_year(self, bus: DesertBus) -> None:
        for day in range(9):
            page = f"https://vst.ninja/{bus.vst_site}/synced_data/day{day}.csv"
            async with self._session.get(page, raise_for_status=False) as req:
                if req.status != 200:
                    break

                data = io.StringIO(await req.text())

            await self._loop.run_in_executor(self._executor, self._process_data, bus, day, data)

    def _process_data(self, year: DesertBus, day: int, data: io.StringIO) -> None:
        event_key = "__" + str(year) + "__"

        data.seek(0)
        reader = csv.reader(data)

        for line_id, line in enumerate(reader):
            event = DBEvent(
                year,
                int(day),
                int(line_id),
                line[0],
                line[3],
                line[7] if line[7] else None,
            )

            self._events[event_key].add(event)
            for word in event.title.lower().split(" "):
                self._events[word].add(event)

        data.close()

    def matches(self, message: str) -> bool:
        lines = message.split("\n")
        return any(line.startswith("!vst ") for line in lines)

    async def process(self, context: MessageContext, message: str) -> bool:
        line = next(line for line in message.split("\n") if line.startswith("!vst "))
        args = line.removeprefix("!vst").lower().split()

        header = f"Searching all years for {' '.join(args)}"
        if args[0].startswith("db"):
            year = int(args[0].removeprefix("db"))
            if year > 2000:
                year -= 2006
            bus = DesertBus(year)
            args[0] = bus.ident
            header = f"Searching {bus.name} for {' '.join(args[1:])}"

        matches = set(self._events[args[0]])
        for arg in args[1:]:
            matches.intersection_update(self._events[arg])

        if not matches:
            await context.reply_all(header + ": no matches found")
            return True

        if len(matches) > 20:
            header += " (filtered to video results due to large number of matches)"
            matches = {m for m in matches if m.link}

        await context.reply_all(
            header + "\n - " + "\n- ".join(map(str, sorted(matches, reverse=True))),
        )
        return True
