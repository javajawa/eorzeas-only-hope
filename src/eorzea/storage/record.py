#!/usr/bin/python3
# vim: ts=4 expandtab

from __future__ import annotations

from typing import Type

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Record:
    name: str
    added_by: str
    added_from: str
    added: datetime = field(default_factory=datetime.utcnow)
    approved: bool = False

    @classmethod
    def from_strings(cls: Type[Record], *args: str) -> Record:
        date = datetime.strptime(args[2], "")
        return cls(args[0], args[1], args[2], date, bool(args[4]))
