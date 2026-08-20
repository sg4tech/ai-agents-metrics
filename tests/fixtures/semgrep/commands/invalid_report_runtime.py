"""Fixture containing an untyped runtime result outside the shared protocol module."""

from typing import Any, Protocol


class ReportRuntime(Protocol):
    def build_report(self) -> Any: ...
