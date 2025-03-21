# SPDX-FileCopyrightText: 2025 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""Final Fantasy XIV Moderation"""

from __future__ import annotations as _future_annotations

import sqlite3
import sys


def main() -> None:
    with sqlite3.connect("list.db") as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM hopes WHERE approved = 0")

        for name, user, channel in cursor.fetchall():
            sys.stdout.write(f"{name:<40}\t{user}:{channel} > ")
            char = input("")

            if char in ["y", "Y"]:
                cursor.execute("UPDATE hopes SET approved = 1 WHERE name = ?", (name,))
            elif char in ["n", "N"]:
                cursor.execute("UPDATE hopes SET approved = -1 WHERE name = ?", (name,))

            connection.commit()


if __name__ == "__main__":
    main()
