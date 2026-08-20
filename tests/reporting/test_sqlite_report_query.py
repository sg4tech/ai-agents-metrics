"""Tests for the SQLite report-query adapter."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

import pytest

from ai_agents_metrics.report.application import WarehouseState, WarehouseStatus
from ai_agents_metrics.report.sqlite_query import SQLiteReportQuery

if TYPE_CHECKING:
    from pathlib import Path

    from pytest import MonkeyPatch


def _create_report_tables(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE derived_projects (
            project_cwd TEXT,
            parent_project_cwd TEXT
        );
        CREATE TABLE normalized_threads (cwd TEXT);
        CREATE TABLE derived_goals (
            thread_id TEXT,
            cwd TEXT,
            last_seen_at TEXT,
            session_count INTEGER,
            model TEXT,
            model_provider TEXT
        );
        CREATE TABLE derived_model_usage (
            thread_id TEXT,
            model TEXT,
            input_tokens INTEGER,
            cache_creation_input_tokens INTEGER,
            cached_input_tokens INTEGER,
            output_tokens INTEGER,
            total_tokens INTEGER
        );
        CREATE TABLE normalized_usage_events (thread_id TEXT, raw_json TEXT);
        CREATE TABLE derived_practice_events (
            thread_id TEXT,
            practice_name TEXT,
            source_kind TEXT
        );
        """
    )


def test_load_report_source_maps_rows_and_merges_projects(tmp_path: Path) -> None:
    warehouse = tmp_path / "warehouse.db"
    with sqlite3.connect(warehouse) as connection:
        _create_report_tables(connection)
        connection.executemany(
            "INSERT INTO derived_goals VALUES (?, ?, ?, ?, ?, ?)",
            [
                ("one", "/projects/first", "2026-01-01", 1, "model", "openai"),
                ("two", "/projects/second", "2026-01-02", 2, "model", "openai"),
                ("three", "/projects/second", "2026-01-02", 3, "model", "openai"),
            ],
        )
        connection.executemany(
            "INSERT INTO derived_model_usage VALUES (?, ?, ?, ?, ?, ?, ?)",
            [("one", "model", 10, 0, 2, 3, 15), ("two", "model", 20, 0, 4, 6, 30)],
        )
        connection.executemany(
            "INSERT INTO derived_practice_events VALUES (?, ?, ?)",
            [("one", "Explore", "Agent"), ("two", "Explore", "Agent")],
        )

    source = SQLiteReportQuery().load_report_source(warehouse)

    assert source.project_cwds == ["/projects/second", "/projects/first"]
    assert source.by_project["/projects/second"].sessions["2026-01-02"] == {
        "threads": 2,
        "sessions": 5,
    }
    assert source.all_projects.sessions == {
        "2026-01-01": {"threads": 1, "sessions": 1},
        "2026-01-02": {"threads": 2, "sessions": 5},
    }
    assert sum(row.total_tokens for row in source.all_projects.tokens) == 45
    assert source.all_projects.practice == [("Explore", "Agent", 2)]


def test_load_report_source_preserves_usage_for_each_model(tmp_path: Path) -> None:
    warehouse = tmp_path / "warehouse.db"
    with sqlite3.connect(warehouse) as connection:
        _create_report_tables(connection)
        connection.execute(
            "INSERT INTO derived_goals VALUES (?, ?, ?, ?, ?, ?)",
            ("mixed", "/project", "2026-01-01", 1, "gpt-second", "openai"),
        )
        connection.executemany(
            "INSERT INTO derived_model_usage VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                ("mixed", "gpt-first", 10, 0, 0, 1, 11),
                ("mixed", "gpt-second", 20, 0, 0, 2, 22),
            ],
        )

    rows = SQLiteReportQuery().load_report_source(warehouse).all_projects.tokens

    assert [(row.model, row.total_tokens) for row in rows] == [
        ("gpt-first", 11),
        ("gpt-second", 22),
    ]


def test_warehouse_state_reports_missing_and_current(tmp_path: Path) -> None:
    warehouse = tmp_path / "warehouse.db"
    query = SQLiteReportQuery()
    assert query.warehouse_state(warehouse, "/repo") == WarehouseState(WarehouseStatus.MISSING_FILE)
    with sqlite3.connect(warehouse) as connection:
        _create_report_tables(connection)
        connection.execute(
            "INSERT INTO derived_goals VALUES ('thread', '/repo', NULL, 1, NULL, NULL)"
        )

    assert query.warehouse_state(warehouse, "/repo") == WarehouseState.ok()


def test_warehouse_state_rejects_outdated_project_schema(tmp_path: Path) -> None:
    warehouse = tmp_path / "warehouse.db"
    with sqlite3.connect(warehouse) as connection:
        connection.execute("CREATE TABLE derived_goals (cwd TEXT)")
        connection.execute("CREATE TABLE derived_practice_events (practice_name TEXT)")
        connection.execute("CREATE TABLE derived_projects (project_cwd TEXT)")

    assert SQLiteReportQuery().warehouse_state(warehouse, "/repo") == WarehouseState(
        WarehouseStatus.SCHEMA_OUTDATED
    )


def test_warehouse_state_rejects_missing_model_usage_table(tmp_path: Path) -> None:
    warehouse = tmp_path / "warehouse.db"
    with sqlite3.connect(warehouse) as connection:
        connection.execute("CREATE TABLE derived_goals (cwd TEXT)")
        connection.execute("CREATE TABLE derived_practice_events (practice_name TEXT)")
        connection.execute(
            "CREATE TABLE derived_projects (project_cwd TEXT, parent_project_cwd TEXT)"
        )

    assert SQLiteReportQuery().warehouse_state(warehouse, "/repo") == WarehouseState(
        WarehouseStatus.SCHEMA_OUTDATED
    )


@pytest.mark.parametrize("cwd", ["/repo", "/repo/.claude/worktrees/feature"])
def test_warehouse_state_includes_child_worktree(tmp_path: Path, cwd: str) -> None:
    warehouse = tmp_path / "warehouse.db"
    with sqlite3.connect(warehouse) as connection:
        _create_report_tables(connection)
        connection.execute(
            "INSERT INTO derived_goals VALUES ('thread', '/repo', NULL, 1, NULL, NULL)"
        )
        connection.execute("INSERT INTO derived_projects VALUES ('/repo', '/repo')")
        connection.execute("INSERT INTO normalized_threads VALUES (?)", (cwd,))

    assert SQLiteReportQuery().warehouse_state(warehouse, cwd) == WarehouseState.ok()


def test_load_report_source_groups_child_worktree_with_parent(tmp_path: Path) -> None:
    warehouse = tmp_path / "warehouse.db"
    with sqlite3.connect(warehouse) as connection:
        _create_report_tables(connection)
        connection.execute("INSERT INTO derived_projects VALUES ('/repo', '/repo')")
        connection.executemany(
            "INSERT INTO normalized_threads VALUES (?)",
            [("/repo",), ("/repo/.claude/worktrees/feature",)],
        )
        connection.executemany(
            "INSERT INTO derived_goals VALUES (?, ?, ?, ?, ?, ?)",
            [
                ("main", "/repo", "2026-01-01T12:00:00Z", 1, "model", "openai"),
                (
                    "child",
                    "/repo/.claude/worktrees/feature",
                    "2026-01-02T12:00:00Z",
                    2,
                    "model",
                    "openai",
                ),
            ],
        )
        connection.executemany(
            "INSERT INTO derived_model_usage VALUES (?, ?, ?, ?, ?, ?, ?)",
            [("main", "model", 10, 0, 0, 1, 11), ("child", "model", 20, 0, 0, 2, 22)],
        )

    source = SQLiteReportQuery().load_report_source(warehouse)

    assert source.project_cwds == ["/repo"]
    assert source.by_project["/repo"].sessions == {
        "2026-01-01": {"threads": 1, "sessions": 1},
        "2026-01-02": {"threads": 1, "sessions": 2},
    }
    assert sum(row.total_tokens for row in source.by_project["/repo"].tokens) == 33


def test_load_report_source_resolves_relative_cwd(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    project = tmp_path / "project"
    project.mkdir()
    warehouse = tmp_path / "warehouse.db"
    with sqlite3.connect(warehouse) as connection:
        _create_report_tables(connection)
        connection.execute("INSERT INTO normalized_threads VALUES (?)", (str(project),))
        connection.execute(
            "INSERT INTO derived_goals VALUES (?, ?, ?, ?, ?, ?)",
            ("thread", str(project), "2026-01-01T12:00:00Z", 1, "model", "openai"),
        )
        connection.execute(
            "INSERT INTO derived_model_usage VALUES ('thread', 'model', 10, 0, 0, 1, 11)"
        )
    monkeypatch.chdir(project)

    source = SQLiteReportQuery().load_report_source(warehouse)

    assert source.by_project[str(project.resolve())].sessions == {
        "2026-01-01": {"threads": 1, "sessions": 1}
    }
