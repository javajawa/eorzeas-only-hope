#!/usr/bin/python3
# vim: ts=4 expandtab

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Set, Type
from random import SystemRandom


RaiseType = Optional[Type[Exception]]


class DataStore(ABC):
    """A data store of names of people who can save Eorzea.

    This base class provides in memory storage, and has two abstract functions
    of `_write_append` for incremental updates and `_write_list` for full
    rebuilds of a backing store, of which one of which SHOULD have a complete
    implementation.
    """

    known: Set[str]
    rand: SystemRandom = SystemRandom()

    def __init__(self: DataStore, values: Optional[Set[str]] = None):
        """Sets up the data store, with the initial set of data that was
        loaded out of the data store"""
        super().__init__()

        # store the initial set of values.
        self.known = values if values is not None else set()
        self.rand = SystemRandom()

    def add(self: DataStore, value: str) -> bool:
        """Adds a value to the DataStore.

        If this value is already in the store, this function is a no-op that
        will always return true.

        Otherwise, this function will return true if the data is successfully
        written to both the in-memory storage and to the backing store."""
        if value in self.known:
            return True

        # Function succeeds iff the backing store if updated,
        # _or_ if this DataStore does not support incremental
        # updates.
        if self._write_append(value) in [False]:
            return False

        self.known.add(value)

        return True

    def random(self: DataStore) -> str:
        """Selects a random element from this store."""

        if not self.known:
            raise Exception("Empty storage")

        return self.rand.sample(self.known, 1)[0]

    @abstractmethod
    def _write_append(self: DataStore, value: str) -> Optional[bool]:
        """Append a value to the underlying data store this type implements.

        This function may be a no-op method, in which case it MUST return None.
        Otherwise, it should return if the write succeeded.

        Values passed to this function SHOULD NOT exist in the store already,
        so the implement does not need to consider de-duplication.
        """

    @abstractmethod
    def _write_list(self: DataStore, value: Set[str]) -> Optional[bool]:
        """Writes an entire list to the backing store, replacing any existing
        list.

        This function may be a no-op, in which case it must always return None.
        Otherwise, it should return whether or not the operation succeeded."""

    def __len__(self: DataStore) -> int:
        return len(self.known)

    def __enter__(self: DataStore) -> DataStore:
        return self

    def __exit__(
        self: DataStore, exception_type: RaiseType, message, traceback
    ) -> Optional[bool]:
        if self._write_list(self.known) in [False]:
            raise Exception("Error writing list to DataStore")

        return exception_type is None
