"""Runtime composition for warehouse summary loading."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai_agents_metrics.history.summary import WarehouseSummary
from ai_agents_metrics.history.summary import load_warehouse_summary as load_summary
from ai_agents_metrics.warehouse.adapters import SQLiteWarehouseGate

if TYPE_CHECKING:
    from pathlib import Path


def load_warehouse_summary(warehouse_path: Path, project_cwd: Path) -> WarehouseSummary:
    return load_summary(warehouse_path, project_cwd, SQLiteWarehouseGate())
