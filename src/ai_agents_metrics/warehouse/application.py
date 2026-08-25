"""Application contracts for warehouse readiness and project scope."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from pathlib import Path

    from ai_agents_metrics.warehouse.domain import (
        BreakdownDimension,
        BreakdownRow,
        BreakdownTokenRecord,
    )


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


@dataclass(frozen=True)
class WarehouseBreakdown:
    schema_version: int
    dimension: BreakdownDimension
    scope: WarehouseScope
    rows: tuple[BreakdownRow, ...]


class WarehouseBreakdownQuery(Protocol):
    def load_records(
        self, warehouse_path: Path, dimension: BreakdownDimension
    ) -> list[BreakdownTokenRecord]: ...


class BreakdownAggregation(Protocol):
    def validate(self, dimension: BreakdownDimension, top: int | None) -> None: ...

    def __call__(
        self,
        records: list[BreakdownTokenRecord],
        dimension: BreakdownDimension,
        top: int | None,
    ) -> tuple[BreakdownRow, ...]: ...


class LoadWarehouseBreakdown:
    def __init__(
        self,
        gate: WarehouseGate,
        query: WarehouseBreakdownQuery,
        aggregator: BreakdownAggregation,
    ) -> None:
        self._gate = gate
        self._query = query
        self._aggregator = aggregator

    def __call__(
        self,
        warehouse_path: Path,
        project_cwd: Path,
        dimension: BreakdownDimension,
        top: int | None,
    ) -> WarehouseBreakdown:
        self._aggregator.validate(dimension, top)
        state = self._gate.resolve(warehouse_path, project_cwd)
        scope = require_warehouse_scope(state, warehouse_path)
        records = self._query.load_records(warehouse_path, dimension)
        scoped_records = (
            records
            if scope.is_all_projects
            else [record for record in records if record.project_cwd == scope.project_cwd]
        )
        rows = self._aggregator(scoped_records, dimension, top)
        return WarehouseBreakdown(
            schema_version=1,
            dimension=dimension,
            scope=scope,
            rows=rows,
        )


def require_warehouse_scope(state: WarehouseState, warehouse_path: Path) -> WarehouseScope:
    if state.status is WarehouseStatus.MISSING_FILE:
        raise ValueError(f"History warehouse does not exist: {warehouse_path}")
    if state.status is not WarehouseStatus.OK or state.scope is None:
        raise ValueError("History warehouse has no derived project data; run history-update first")
    return state.scope
