"""Fixture containing a handler coupled to an aggregate runtime."""

from typing import Protocol


class CommandRuntime(Protocol):
    def build_report(self) -> str: ...


def handle_report(runtime: CommandRuntime) -> None:
    runtime.build_report()
