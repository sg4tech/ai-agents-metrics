"""Application contracts for warehouse readiness and project scope."""

from __future__ import annotations

from dataclasses import dataclass, replace
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


class BreakdownDimension(StrEnum):
    MODEL = "model"
    PROJECT = "project"
    CATEGORY = "token-type"


@dataclass(frozen=True)
class BreakdownTokenRecord:
    key: str
    project_cwd: str
    input_tokens: int | None
    cache_creation_input_tokens: int | None
    cached_input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None


@dataclass(frozen=True)
class BreakdownRow:
    key: str
    input_tokens: int | None
    cache_creation_input_tokens: int | None
    cached_input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None
    share_of_total: float
    grouped_row_count: int = 1
    is_remainder: bool = False


@dataclass(frozen=True)
class WarehouseBreakdown:
    schema_version: int
    dimension: BreakdownDimension
    scope: WarehouseScope
    rows: list[BreakdownRow]


class WarehouseBreakdownQuery(Protocol):
    def load_records(
        self, warehouse_path: Path, dimension: BreakdownDimension
    ) -> list[BreakdownTokenRecord]: ...


class LoadWarehouseBreakdown:
    def __init__(self, gate: WarehouseGate, query: WarehouseBreakdownQuery) -> None:
        self._gate = gate
        self._query = query

    def __call__(
        self,
        warehouse_path: Path,
        project_cwd: Path,
        dimension: BreakdownDimension,
        top: int | None,
    ) -> WarehouseBreakdown:
        if top is not None and top <= 0:
            raise ValueError("--top must be a positive integer")
        if dimension is BreakdownDimension.CATEGORY and top is not None:
            raise ValueError("--top is not supported with --by token-type")
        state = self._gate.resolve(warehouse_path, project_cwd)
        scope = require_warehouse_scope(state, warehouse_path)
        records = self._query.load_records(warehouse_path, dimension)
        scoped_records = (
            records
            if scope.is_all_projects
            else [record for record in records if record.project_cwd == scope.project_cwd]
        )
        rows = _aggregate_records(scoped_records)
        if dimension is BreakdownDimension.CATEGORY:
            rows = _token_type_rows(rows)
        rows = _with_shares(rows)
        if top is not None:
            rows = _apply_top(rows, top)
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


def _sum_optional(values: list[int | None]) -> int | None:
    known_values = [value for value in values if value is not None]
    return sum(known_values) if known_values else None


def _aggregate_records(records: list[BreakdownTokenRecord]) -> list[BreakdownRow]:
    grouped: dict[str, list[BreakdownTokenRecord]] = {}
    for record in records:
        grouped.setdefault(record.key, []).append(record)
    return sorted(
        (
            BreakdownRow(
                key=key,
                input_tokens=_sum_optional([record.input_tokens for record in group]),
                cache_creation_input_tokens=_sum_optional(
                    [record.cache_creation_input_tokens for record in group]
                ),
                cached_input_tokens=_sum_optional([record.cached_input_tokens for record in group]),
                output_tokens=_sum_optional([record.output_tokens for record in group]),
                total_tokens=_sum_optional([record.total_tokens for record in group]),
                share_of_total=0.0,
                grouped_row_count=1,
            )
            for key, group in grouped.items()
        ),
        key=lambda row: (-(row.total_tokens or 0), row.key),
    )


def _token_type_rows(rows: list[BreakdownRow]) -> list[BreakdownRow]:
    totals = BreakdownRow(
        key="totals",
        input_tokens=_sum_optional([row.input_tokens for row in rows]),
        cache_creation_input_tokens=_sum_optional(
            [row.cache_creation_input_tokens for row in rows]
        ),
        cached_input_tokens=_sum_optional([row.cached_input_tokens for row in rows]),
        output_tokens=_sum_optional([row.output_tokens for row in rows]),
        total_tokens=_sum_optional([row.total_tokens for row in rows]),
        share_of_total=0.0,
    )
    token_rows = [
        BreakdownRow(
            key="input",
            input_tokens=totals.input_tokens,
            cache_creation_input_tokens=None,
            cached_input_tokens=None,
            output_tokens=None,
            total_tokens=totals.input_tokens,
            share_of_total=0.0,
        ),
        BreakdownRow(
            key="cache_creation",
            input_tokens=None,
            cache_creation_input_tokens=totals.cache_creation_input_tokens,
            cached_input_tokens=None,
            output_tokens=None,
            total_tokens=totals.cache_creation_input_tokens,
            share_of_total=0.0,
        ),
        BreakdownRow(
            key="cached",
            input_tokens=None,
            cache_creation_input_tokens=None,
            cached_input_tokens=totals.cached_input_tokens,
            output_tokens=None,
            total_tokens=totals.cached_input_tokens,
            share_of_total=0.0,
        ),
        BreakdownRow(
            key="output",
            input_tokens=None,
            cache_creation_input_tokens=None,
            cached_input_tokens=None,
            output_tokens=totals.output_tokens,
            total_tokens=totals.output_tokens,
            share_of_total=0.0,
        ),
    ]
    return sorted(token_rows, key=lambda row: (-(row.total_tokens or 0), row.key))


def _with_shares(rows: list[BreakdownRow]) -> list[BreakdownRow]:
    grand_total = sum(row.total_tokens or 0 for row in rows)
    return [
        replace(
            row,
            share_of_total=((row.total_tokens or 0) / grand_total if grand_total else 0.0),
        )
        for row in rows
    ]


def _apply_top(rows: list[BreakdownRow], top: int) -> list[BreakdownRow]:
    if len(rows) <= top:
        return rows
    visible = rows[:top]
    hidden = rows[top:]
    other = BreakdownRow(
        key="other",
        input_tokens=_sum_optional([row.input_tokens for row in hidden]),
        cache_creation_input_tokens=_sum_optional(
            [row.cache_creation_input_tokens for row in hidden]
        ),
        cached_input_tokens=_sum_optional([row.cached_input_tokens for row in hidden]),
        output_tokens=_sum_optional([row.output_tokens for row in hidden]),
        total_tokens=_sum_optional([row.total_tokens for row in hidden]),
        share_of_total=sum(row.share_of_total for row in hidden),
        grouped_row_count=len(hidden),
        is_remainder=True,
    )
    return [*visible, other]
