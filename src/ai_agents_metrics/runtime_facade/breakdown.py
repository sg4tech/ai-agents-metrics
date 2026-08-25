"""Runtime composition for warehouse token breakdowns."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai_agents_metrics.warehouse.adapters import (
    SQLiteWarehouseBreakdownQuery,
    SQLiteWarehouseGate,
)
from ai_agents_metrics.warehouse.application import (
    LoadWarehouseBreakdown,
    WarehouseBreakdown,
)
from ai_agents_metrics.warehouse.domain import BreakdownAggregator, BreakdownDimension

if TYPE_CHECKING:
    from pathlib import Path


def load_warehouse_breakdown(
    warehouse_path: Path,
    project_cwd: Path,
    dimension: BreakdownDimension,
    top: int | None,
) -> WarehouseBreakdown:
    use_case = LoadWarehouseBreakdown(
        SQLiteWarehouseGate(),
        SQLiteWarehouseBreakdownQuery(),
        BreakdownAggregator(),
    )
    return use_case(warehouse_path, project_cwd, dimension, top)
