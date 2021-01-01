#!/usr/bin/env python3
# vim: ts=4 expandtab

"""Storage system for the character names."""

from __future__ import annotations

from .datastore import DataStore
from .filestore import FileStore
from .sqlite import SQLite


__all__ = ["DataStore", "FileStore", "SQLite"]
