#!/usr/bin/python3
# vim: ts=4 expandtab

# from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Type, Set
from random import SystemRandom


class DataStore(ABC):
    """A datastore of names of people who can save Eorzea.

    This base class provides in memory storage, and has two abstract functions
    of `_write_append` for incremental updates and `_write_list` for full
    rebuilds of a backing store, of which one of which SHOULD have a complete
    implementation.
    """

    #TODO: known: Set[str]
    #TODO: rand: SystemRandom = SystemRandom()

    def __init__(self: Type['DataStore'], values: Optional[Set[str]] = None):
        """Sets up the datastore, with the initial set of data that was
        loaded out of the datastore"""
        super().__init__()

        # store the initial set of values.
        self.known = values if values is not None else set()
        self.rand = SystemRandom()

    def add(self: Type['DataStore'], value: str) -> bool:
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
        if self._write_append(value) == False:
            return False

        # TODO: check if we're throwing away a return here.
        self.known.add(value)

        return True


    def random(self: Type['DataStore']) -> str:
        """Selects a random element from this store."""

        if not len(self.known):
            raise Exception("Empty storage")

        return self.rand.sample(self.known, 1)[0]

    @abstractmethod
    def _write_append(self: Type['DataStore'], value: str) -> Optional[bool]:
        """Append a value to the underlying datstore this type implements.

        This function may be a no-op method, in which case it MUST return None.
        Otherwise, it should return if the write succeded.

        Values passed to this function SHOULD NOT exist in the store already,
        so the implement does not need to consider de-duplication.
        """
        pass

    @abstractmethod
    def _write_list(self: Type['DataStore'], value: Set[str]) -> Optional[bool]:
        pass

    def __len__(self: Type['DataStore']) -> int:
        return len(self.known)

    def __enter__(self: Type['DataStore']) -> 'DataStore':
        return self

    def __exit__(self: Type['DataStore'], exception_type: Optional[Type[Exception]] = None, exception_message = None, traceback = None) -> bool:
        # TODO: Error handling here.
        self._write_list(self.known)

        return exception_type is None
