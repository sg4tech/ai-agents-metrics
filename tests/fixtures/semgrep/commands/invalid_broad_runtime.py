"""Fixture containing a handler coupled to an aggregate runtime."""

from argparse import Namespace
from typing import Protocol


class CliRuntime(Protocol):
    def build_report(self) -> str: ...


def handle_report(_args: Namespace, runtime: CliRuntime) -> None:
    runtime.build_report()
