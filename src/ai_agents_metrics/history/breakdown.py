"""Composition and renderers for warehouse token breakdowns."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import TYPE_CHECKING

from ai_agents_metrics.warehouse import SQLiteWarehouseGate
from ai_agents_metrics.warehouse.application import (
    BreakdownDimension,
    LoadWarehouseBreakdown,
    WarehouseBreakdown,
)
from ai_agents_metrics.warehouse.sqlite_breakdown import SQLiteWarehouseBreakdownQuery

if TYPE_CHECKING:
    from pathlib import Path


def load_warehouse_breakdown(
    warehouse_path: Path,
    project_cwd: Path,
    dimension: BreakdownDimension,
    top: int | None,
) -> WarehouseBreakdown:
    return LoadWarehouseBreakdown(SQLiteWarehouseGate(), SQLiteWarehouseBreakdownQuery())(
        warehouse_path, project_cwd, dimension, top
    )


def render_warehouse_breakdown_json(breakdown: WarehouseBreakdown) -> str:
    return json.dumps(asdict(breakdown), indent=2, sort_keys=True)


def render_warehouse_breakdown(breakdown: WarehouseBreakdown) -> str:
    scope = "all projects" if breakdown.scope.is_all_projects else breakdown.scope.project_cwd
    lines = [
        f"AI Agents Metrics — Token Breakdown by {breakdown.dimension.value}",
        f"Scope: {scope}",
        "Key | Input | Cache created | Cached | Output | Total | Share",
    ]
    lines.extend(
        " | ".join(
            (
                _row_label(row.key, row.grouped_row_count, row.is_remainder),
                _tokens(row.input_tokens),
                _tokens(row.cache_creation_input_tokens),
                _tokens(row.cached_input_tokens),
                _tokens(row.output_tokens),
                _tokens(row.total_tokens),
                f"{row.share_of_total:.2%}",
            )
        )
        for row in breakdown.rows
    )
    return "\n".join(lines)


def _tokens(value: int | None) -> str:
    return "n/a" if value is None else str(value)


def _row_label(key: str, grouped_row_count: int, is_remainder: bool) -> str:
    return f"other ({grouped_row_count} rows)" if is_remainder else key
