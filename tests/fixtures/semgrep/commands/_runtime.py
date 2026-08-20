"""Fixture containing an untyped runtime result boundary."""

from typing import Any, Protocol


class InvalidRuntime(Protocol):
    def execute(self) -> Any: ...
