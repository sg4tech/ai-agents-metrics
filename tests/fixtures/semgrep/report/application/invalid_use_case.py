"""Fixture containing direct I/O in a nested application use-case module."""

import sqlite3


def build_report(path: object) -> None:
    sqlite3.connect(path)  # type: ignore[arg-type]
