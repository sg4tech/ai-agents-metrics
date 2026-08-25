"""SQLite adapter tests for warehouse breakdown records."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

from ai_agents_metrics.warehouse.domain import BreakdownDimension
from ai_agents_metrics.warehouse.sqlite_breakdown import SQLiteWarehouseBreakdownQuery

if TYPE_CHECKING:
    from pathlib import Path


def test_project_records_fall_back_to_project_cwd(tmp_path: Path) -> None:
    warehouse = tmp_path / "warehouse.db"
    with sqlite3.connect(warehouse) as connection:
        connection.execute(
            "CREATE TABLE derived_projects (project_cwd TEXT, parent_project_cwd TEXT, "
            "input_tokens INTEGER, cache_creation_input_tokens INTEGER, "
            "cached_input_tokens INTEGER, output_tokens INTEGER, total_tokens INTEGER)"
        )
        connection.execute(
            "INSERT INTO derived_projects VALUES ('/project', NULL, 10, 0, 0, 0, 10)"
        )

    records = SQLiteWarehouseBreakdownQuery().load_records(
        warehouse, BreakdownDimension.PROJECT
    )

    assert [(record.key, record.project_cwd) for record in records] == [
        ("/project", "/project")
    ]


def test_model_records_ignore_goals_without_cwd(tmp_path: Path) -> None:
    warehouse = tmp_path / "warehouse.db"
    with sqlite3.connect(warehouse) as connection:
        connection.execute("CREATE TABLE derived_goals (thread_id TEXT, cwd TEXT)")
        connection.execute(
            "CREATE TABLE derived_model_usage (thread_id TEXT, model TEXT, "
            "input_tokens INTEGER, cache_creation_input_tokens INTEGER, "
            "cached_input_tokens INTEGER, output_tokens INTEGER, total_tokens INTEGER)"
        )
        connection.execute("INSERT INTO derived_goals VALUES ('thread', NULL)")
        connection.execute(
            "INSERT INTO derived_model_usage VALUES ('thread', 'model', 10, 0, 0, 0, 10)"
        )

    records = SQLiteWarehouseBreakdownQuery().load_records(warehouse, BreakdownDimension.MODEL)

    assert records == []
