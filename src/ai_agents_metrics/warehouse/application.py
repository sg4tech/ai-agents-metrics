"""Application contracts for warehouse readiness and project scope."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from pathlib import Path


class WarehouseStatus(StrEnum):
    OK = "ok"
    MISSING_FILE = "missing_file"
    SCHEMA_OUTDATED = "schema_outdated"
    EMPTY_FOR_CWD = "empty_for_cwd"


@dataclass(frozen=True)
class WarehouseScope:
    project_cwd: str
    is_all_projects: bool


@dataclass(frozen=True)
class WarehouseState:
    status: WarehouseStatus
    scope: WarehouseScope | None = None

    @classmethod
    def ok(cls, scope: WarehouseScope | None = None) -> WarehouseState:
        return cls(WarehouseStatus.OK, scope)

    def as_render_data(self) -> dict[str, str]:
        return {"status": self.status.value}


class WarehouseGate(Protocol):
    def resolve(self, warehouse_path: Path, project_cwd: Path) -> WarehouseState: ...
