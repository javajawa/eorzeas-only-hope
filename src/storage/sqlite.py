#!/usr/bin/python3
# vim: ts=4 expandtab

from __future__ import annotations

from typing import Optional, Set

import sqlite3

from .datastore import DataStore, RaiseType


class SQLite(DataStore):
    """Datastore backed in SQLite 3"""

    conn: sqlite3.Connection
    cursor: sqlite3.Cursor

    def __init__(self: SQLite, file_name: str):
        """Sets up the data store"""

        super().__init__(None)

        self.conn = sqlite3.connect(file_name)
        self.cursor = self.conn.cursor()
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS hopes (
                name text
            )
        """
        )
        self.conn.commit()

    def _write_append(self: SQLite, value: str) -> Optional[bool]:
        """Append a value to the underlying data store this type implements.

        This function may be a no-op method, in which case it MUST return None.
        Otherwise, it should return if the write succeeded.

        Values passed to this function SHOULD NOT exist in the store already,
        so the implement does not need to consider de-duplication.
        """

        self.cursor.execute("INSERT OR IGNORE INTO hopes (name) VALUES (?)", (value,))
        self.conn.commit()

        return True

    def random(self: SQLite) -> str:
        """Selects a random element from this store."""

        self.cursor.execute("SELECT name FROM hopes ORDER BY RANDOM() LIMIT 1")
        row = self.cursor.fetchone()

        return row[0] if row else "???"

    def __len__(self: SQLite) -> int:
        self.cursor.execute("SELECT COUNT(0) FROM hopes")

        return int(self.cursor.fetchone()[0])

    def _write_list(self: SQLite, value: Set[str]) -> Optional[bool]:
        return None

    def __exit__(
        self: SQLite, exception_type: RaiseType, message, traceback
    ) -> Optional[bool]:
        self.conn.commit()
        self.conn.close()

        return super().__exit__(exception_type, message, traceback)
