"""SQLite adapter for typed warehouse breakdown records."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING, TypeAlias

from ai_agents_metrics.history.project_paths import parent_project_cwd
from ai_agents_metrics.warehouse.domain import (
    BreakdownDimension,
    BreakdownTokenRecord,
)

if TYPE_CHECKING:
    from pathlib import Path

BreakdownDbRow: TypeAlias = tuple[
    str | None,
    str,
    int | None,
    int | None,
    int | None,
    int | None,
    int | None,
]

_PROJECT_RECORDS_QUERY = """
    SELECT COALESCE(parent_project_cwd, project_cwd),
           COALESCE(parent_project_cwd, project_cwd), input_tokens,
           cache_creation_input_tokens, cached_input_tokens, output_tokens, total_tokens
    FROM derived_projects
    WHERE COALESCE(parent_project_cwd, project_cwd) IS NOT NULL
      AND COALESCE(parent_project_cwd, project_cwd) != ''
"""
_MODEL_RECORDS_QUERY = """
    SELECT dmu.model, dg.cwd, dmu.input_tokens, dmu.cache_creation_input_tokens,
           dmu.cached_input_tokens, dmu.output_tokens, dmu.total_tokens
    FROM derived_model_usage dmu
    JOIN derived_goals dg ON dg.thread_id = dmu.thread_id
    WHERE dg.cwd IS NOT NULL AND dg.cwd != ''
"""


class SQLiteWarehouseBreakdownQuery:
    def load_records(
        self, warehouse_path: Path, dimension: BreakdownDimension
    ) -> list[BreakdownTokenRecord]:
        query = (
            _MODEL_RECORDS_QUERY
            if dimension is BreakdownDimension.MODEL
            else _PROJECT_RECORDS_QUERY
        )
        try:
            with sqlite3.connect(warehouse_path) as connection:
                rows: list[BreakdownDbRow] = connection.execute(query).fetchall()
        except sqlite3.DatabaseError as exc:
            raise ValueError(f"Cannot read history warehouse: {exc}") from exc
        return [self._map_record(row, dimension) for row in rows]

    @staticmethod
    def _map_record(row: BreakdownDbRow, dimension: BreakdownDimension) -> BreakdownTokenRecord:
        raw_key, raw_cwd, input_tokens, cache_creation, cached, output, total = row
        project_cwd = parent_project_cwd(raw_cwd) or raw_cwd
        key = project_cwd if dimension is BreakdownDimension.PROJECT else (raw_key or "unknown")
        return BreakdownTokenRecord(
            key=key,
            project_cwd=project_cwd,
            input_tokens=input_tokens,
            cache_creation_input_tokens=cache_creation,
            cached_input_tokens=cached,
            output_tokens=output,
            total_tokens=total,
        )
