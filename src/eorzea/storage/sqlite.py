#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

# vim: ts=4 expandtab

"""Data store backed in SQLite 3"""

from __future__ import annotations

from typing import Any, List, Optional

import sqlite3

from .datastore import DataStore, RaiseType
from .record import Record


class SQLite(DataStore):
    """Data store backed in SQLite 3"""

    conn: sqlite3.Connection
    cursor: sqlite3.Cursor

    def __init__(self, file_name: str):
        """Sets up the data store"""

        super().__init__()

        self.conn = sqlite3.connect(file_name)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS hopes (
                name        text UNIQUE,
                added_by    text,
                added_from  text,
                added       timestamp DEFAULT CURRENT_TIMESTAMP,
                approved    bool
            )
        """
        )
        self.conn.commit()

    def _write_append(self, record: Record) -> Optional[bool]:
        """Append a record to the underlying data store this type implements.

        This function may be a no-op method, in which case it MUST return None.
        Otherwise, it should return if the write succeeded.

        Values passed to this function SHOULD NOT exist in the store already,
        so the implement does not need to consider de-duplication.
        """

        self.cursor.execute(
            "INSERT OR IGNORE INTO hopes VALUES (?,?,?,?,?)",
            (record.name, record.added_by, record.added_from, record.added, record.approved),
        )
        self.conn.commit()

        return True

    def random(self) -> Record:
        """Selects a random element from this store."""

        self.cursor.execute(
            "SELECT * FROM hopes WHERE approved = true ORDER BY RANDOM() LIMIT 1"
        )

        record = Record(**self.cursor.fetchone())
        self.seen.add(record.name)

        return record

    def __len__(self) -> int:
        self.cursor.execute("SELECT COUNT(0) FROM hopes WHERE approved == true")

        return int(self.cursor.fetchone()[0])

    def _write_list(self, _: Optional[List[Record]]) -> Optional[bool]:
        return None

    def __exit__(
        self, exception_type: RaiseType, message: Any, traceback: Any
    ) -> Optional[bool]:
        self.conn.commit()
        self.conn.close()

        return super().__exit__(exception_type, message, traceback)
