"""Tests for the shared SQLite warehouse gate."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

from ai_agents_metrics.warehouse import WarehouseStatus
from ai_agents_metrics.warehouse.adapters import SQLiteWarehouseGate

if TYPE_CHECKING:
    from pathlib import Path


def _create_schema(path: Path, *, include_model_usage: bool = True) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute(
            "CREATE TABLE derived_projects (project_cwd TEXT, parent_project_cwd TEXT)"
        )
        connection.execute("CREATE TABLE derived_goals (cwd TEXT)")
        connection.execute("CREATE TABLE derived_practice_events (practice_name TEXT)")
        if include_model_usage:
            connection.execute("CREATE TABLE derived_model_usage (model TEXT)")


def test_gate_reports_missing_file(tmp_path: Path) -> None:
    state = SQLiteWarehouseGate().resolve(tmp_path / "missing.db", tmp_path)

    assert state.status is WarehouseStatus.MISSING_FILE
    assert state.scope is None


def test_gate_reports_outdated_schema(tmp_path: Path) -> None:
    warehouse = tmp_path / "warehouse.db"
    _create_schema(warehouse, include_model_usage=False)

    state = SQLiteWarehouseGate().resolve(warehouse, tmp_path)

    assert state.status is WarehouseStatus.SCHEMA_OUTDATED
    assert state.scope is None


def test_gate_reports_empty_warehouse_for_cwd(tmp_path: Path) -> None:
    warehouse = tmp_path / "warehouse.db"
    _create_schema(warehouse)

    state = SQLiteWarehouseGate().resolve(warehouse, tmp_path)

    assert state.status is WarehouseStatus.EMPTY_FOR_CWD
    assert state.scope is None


def test_gate_reports_ok_for_matching_project(tmp_path: Path) -> None:
    warehouse = tmp_path / "warehouse.db"
    project = tmp_path / "project"
    _create_schema(warehouse)
    with sqlite3.connect(warehouse) as connection:
        connection.execute(
            "INSERT INTO derived_projects VALUES (?, ?)", (str(project), str(project))
        )

    state = SQLiteWarehouseGate().resolve(warehouse, project)

    assert state.status is WarehouseStatus.OK
    assert state.scope is not None
    assert state.scope.project_cwd == str(project)
    assert not state.scope.is_all_projects


def test_gate_falls_back_to_all_projects(tmp_path: Path) -> None:
    warehouse = tmp_path / "warehouse.db"
    _create_schema(warehouse)
    with sqlite3.connect(warehouse) as connection:
        connection.execute(
            "INSERT INTO derived_projects VALUES ('/another/project', '/another/project')"
        )

    state = SQLiteWarehouseGate().resolve(warehouse, tmp_path / "missing-project")

    assert state.status is WarehouseStatus.OK
    assert state.scope is not None
    assert state.scope.is_all_projects
