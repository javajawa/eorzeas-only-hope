#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import json
from typing import Any, Coroutine, Dict, Tuple

import os

import aiofiles
import aiohttp

from prosegen import ProseGen


def get_ffxiv_quotes(
    loop: asyncio.AbstractEventLoop, *characters: str
) -> Tuple[Dict[str, ProseGen], Coroutine[None]]:
    datasets: Dict[str, ProseGen] = {name: ProseGen(16) for name in characters}

    task = load_ffix_quotes(loop, datasets)

    return datasets, task


async def load_ffix_quotes(
    loop: asyncio.AbstractEventLoop, datasets: Dict[str, ProseGen]
) -> None:
    print("Beginning loading of quotes")

    tasks = []

    async with aiohttp.ClientSession() as session:
        print("Request quest index")
        async with session.get(
            "https://garlandtools.org/db/doc/browse/en/2/quest.json"
        ) as resp:
            quests_json = await resp.json()

            quests = [quest["i"] for quest in quests_json["browse"]]

            for quest in quests:
                tasks.append(loop.create_task(load_quest_data(session, datasets, quest)))

    await asyncio.gather(*tasks)
    print("Finished loading data")


async def load_quest_data(
    session: aiohttp.ClientSession, datasets: Dict[str, ProseGen], quest: str
) -> None:
    quest_json = await load_json_with_cache(
        session,
        f"https://garlandtools.org/db/doc/quest/en/2/{quest}.json",
        f"quest-{quest}",
    )

    lines = 0

    for line in quest_json["quest"]["dialogue"]:
        if line["name"] not in datasets:
            continue

        datasets[line["name"]].add_knowledge(line["text"])
        lines += 1


async def load_json_with_cache(session: aiohttp.ClientSession, url: str, key: str) -> Any:
    cache_path = os.path.join("caches", key)

    if os.path.exists(cache_path):
        async with aiofiles.open(cache_path, "r", encoding="utf-8") as cached_file:
            return json.loads(await cached_file.read())

    async with session.get(url) as resp:
        async with aiofiles.open(cache_path, "w", encoding="utf-8") as cached_file:
            await cached_file.write(await resp.text())

        return await resp.json()


if __name__ == "__main__":
    os.makedirs("caches", exist_ok=True)
    _loop = asyncio.get_event_loop()
    print(get_ffxiv_quotes(_loop, "URIANGER", "ALISAIE"))
    _loop.run_forever()
