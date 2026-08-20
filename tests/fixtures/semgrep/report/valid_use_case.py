"""Fixture containing application orchestration through a port."""

from typing import Protocol


class ReportPort(Protocol):
    def load(self) -> str: ...


def build_report(port: ReportPort) -> str:
    return port.load()
