# SPDX-FileCopyrightText: 2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""A data store of names of people who can save Eorzea, written to a file
with one entry per line"""

from __future__ import annotations as _future_annotations

from types import TracebackType
from typing import TextIO

import pathlib

from .datastore import DataStore
from .record import Record


class FileStore(DataStore):
    """A data store of names of people who can save Eorzea, written to a file
    with one entry per line"""

    file_handle: TextIO

    def __init__(self, file_name: pathlib.Path) -> None:
        """Sets up the data store, reading the data set
        from the file if needed"""

        from_storage: list[Record] | None = None

        if file_name.exists():
            with file_name.open(encoding="utf-8") as handle:
                lines = [line.strip() for line in handle]
                from_storage = [Record.from_strings(*p.split("\t")) for p in lines]

        super().__init__(from_storage)

        # pylint: disable=consider-using-with
        self.file_handle = file_name.open("a", encoding="utf-8")

    def _write_append(self, record: Record) -> bool | None:
        """Append a value to the underlying data store this type implements.

        This function may be a no-op method, in which case it MUST return None.
        Otherwise, it should return if the write succeeded.

        Values passed to this function SHOULD NOT exist in the store already,
        so the implement does not need to consider de-duplication.
        """
        return self.file_handle.write(f"{record}\n") > 0

    def _write_list(self, _: list[Record]) -> bool | None:
        return None

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.file_handle.close()
        super().__exit__(exception_type, exception, traceback)
