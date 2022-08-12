#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""A data store of names of people who can save Eorzea, written to a file
with one entry per line"""

from __future__ import annotations

from typing import Any, List, Optional, TextIO
from os.path import exists as path_exists

from .datastore import DataStore, RaiseType
from .record import Record


class FileStore(DataStore):
    """A data store of names of people who can save Eorzea, written to a file
    with one entry per line"""

    file_handle: TextIO

    def __init__(self, file_name: str):
        """Sets up the data store, reading the data set
        from the file if needed"""

        from_storage: Optional[List[Record]] = None

        if path_exists(file_name):
            with open(file_name, "rt", encoding="utf-8") as handle:
                lines = [line.strip() for line in handle]
                from_storage = [Record.from_strings(*p.split("\t")) for p in lines]

        super().__init__(from_storage)

        # pylint: disable=consider-using-with
        self.file_handle = open(file_name, "a", encoding="utf-8")

    def _write_append(self, record: Record) -> Optional[bool]:
        """Append a value to the underlying data store this type implements.

        This function may be a no-op method, in which case it MUST return None.
        Otherwise, it should return if the write succeeded.

        Values passed to this function SHOULD NOT exist in the store already,
        so the implement does not need to consider de-duplication.
        """
        return self.file_handle.write(f"{record}\n") > 0

    def _write_list(self, _: List[Record]) -> Optional[bool]:
        return None

    def __exit__(
        self, exception_type: RaiseType, message: Any, traceback: Any
    ) -> Optional[bool]:
        self.file_handle.close()

        return super().__exit__(exception_type, message, traceback)
