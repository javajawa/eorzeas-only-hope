# SPDX-FileCopyrightText: 2025 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations as _future_annotations

from typing import NamedTuple

import collections
import csv
import json
import pathlib
import sys

words = [
    "No Info",
    "He/Him",
    "She/Her",
    "He/She",
    "They/Them",
    "He/They",
    "She/They",
    "Any/All",
]


class PronounSet(NamedTuple):
    he: bool
    she: bool
    they: bool

    def __str__(self) -> str:
        acc = 0
        acc += 1 if self.he else 0
        acc += 2 if self.she else 0
        acc += 4 if self.they else 0

        return words[acc]


counts: collections.Counter[PronounSet] = collections.Counter()


def main() -> None:
    with (pathlib.Path.cwd().parent / "users.csv").open(encoding="utf-8") as users:
        reader = csv.reader(users)
        for row in reader:
            he = she = they = False

            roles = json.loads(row[4].replace("'", '"'))
            if "he/him" in roles or "he/they" in roles:
                he = True
            if "she/her" in roles or "she/they" in roles:
                she = True
            if "he/they" in roles or "she/they" in roles or "they/them" in roles:
                they = True

            counts[PronounSet(he, she, they)] += 1

    for group, count in counts.items():
        sys.stdout.write(f"{group:40s} {count}")


if __name__ == "__main__":
    main()
