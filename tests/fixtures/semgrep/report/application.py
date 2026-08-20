"""Fixture containing direct I/O in an application module."""

import sqlite3


def build_report(path: object) -> None:
    sqlite3.connect(path)  # type: ignore[arg-type]
    path.write_text("report", encoding="utf-8")  # type: ignore[attr-defined]
