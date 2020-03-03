#!/usr/bin/python3
# vim: ts=4 expandtab

# from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Type, Set
from os.path import exists as path_exists

from .datastore import DataStore

class FileStore(DataStore):
    """A datastore of names of people who can save Eorzea, written to a file
    with one entry per line"""

    # TODO: file_handle: TextIO

    def __init__(self: Type['FileStore'], file_name: str):
        """Sets up the datastore, reading the dataset from the file if needed"""

        # TODO: from_storage: Optional[Set[str]] = None
        from_storage = None

        if path_exists(file_name):
            with open(file_name, 'r') as handle:
                from_storage = set([line.strip() for line in handle])
                print(from_storage)

        super().__init__(from_storage)

        # TODO: Look up the close/with interface
        self.file_handle = open(file_name, 'a')

    def _write_append(self: Type[DataStore], value: str) -> Optional[bool]:
        """Append a value to the underlying datstore this type implements.

        This function may be a no-op method, in which case it MUST return None.
        Otherwise, it should return if the write succeded.

        Values passed to this function SHOULD NOT exist in the store already,
        so the implement does not need to consider de-duplication.
        """
        return self.file_handle.write("%s\n" % value)

    def _write_list(self: Type[DataStore], value: Set[str]) -> Optional[bool]:
        return None

    def __exit__(self: Type['FileStore'], exception_type: Optional[Type[Exception]], excpetion_message, traceback) -> bool:
        super().__exit__()
        self.file_handle.close()

        return exception_type is None
