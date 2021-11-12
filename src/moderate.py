#!/usr/bin/env python3
# vim: ts=4 expandtab

"""Final Fantasy XIV Moderation"""

from __future__ import annotations

import sqlite3


def main() -> None:
    with sqlite3.connect("/srv/eorzea/list.db") as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM hopes WHERE approved = 0")

        for record in cursor.fetchall():
            print("{:<40}\t{}:{} >".format(*record[0:3]), end="")
            char = input("")

            if char in ["y", "Y"]:
                cursor.execute("UPDATE hopes SET approved = 1 WHERE name = ?", (record[0],))
            elif char in ["n", "N"]:
                cursor.execute("UPDATE hopes SET approved = -1 WHERE name = ?", (record[0],))

            connection.commit()


if __name__ == "__main__":
    main()
