from __future__ import annotations

import json
from typing import Any, Dict

import os

import requests

from prosegen import ProseGen


def get_ffxiv_quotes(*characters: str) -> Dict[str, ProseGen]:
    datasets: Dict[str, ProseGen] = {name: ProseGen(16) for name in characters}

    with requests.Session() as session:
        quests_json = session.get(
            "https://garlandtools.org/db/doc/browse/en/2/quest.json"
        ).json()
        quests = [quest["i"] for quest in quests_json["browse"]]

        for quest in quests:
            quest_json = load_json_with_cache(
                session,
                f"https://garlandtools.org/db/doc/quest/en/2/{quest}.json",
                f"quest-{quest}",
            )

            for line in quest_json["quest"]["dialogue"]:
                if line["name"] not in datasets:
                    continue

                datasets[line["name"]].add_knowledge(line["text"])

    return datasets


def load_json_with_cache(session: requests.Session, url: str, key: str) -> Any:
    cache_path = os.path.join("caches", key)

    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as cached_file:
            return json.load(cached_file)

    print("Fetching", url)
    data = session.get(url)

    with open(cache_path, "w", encoding="utf-8") as cached_file:
        cached_file.write(data.text)

    return data.json()


if __name__ == "__main__":
    os.makedirs("caches", exist_ok=True)
    get_ffxiv_quotes()
