#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""Storage system for the character names."""

from __future__ import annotations

from .datastore import DataStore
from .filestore import FileStore
from .sqlite import SQLite


__all__ = ["DataStore", "FileStore", "SQLite"]
