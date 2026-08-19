"""Tests for warehouse-native CLI summary queries."""
from __future__ import annotations

import json
import sqlite3
from typing import TYPE_CHECKING

import pytest

from ai_agents_metrics.history.summary import load_warehouse_summary, render_warehouse_summary_json

if TYPE_CHECKING:
    from pathlib import Path


def _create_warehouse(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE derived_projects (
                project_cwd TEXT PRIMARY KEY, parent_project_cwd TEXT, thread_count INTEGER,
                attempt_count INTEGER, retry_thread_count INTEGER, message_count INTEGER,
                usage_event_count INTEGER, input_tokens INTEGER,
                cache_creation_input_tokens INTEGER, cached_input_tokens INTEGER,
                output_tokens INTEGER, total_tokens INTEGER,
                total_tokens_covered_sessions INTEGER, first_seen_at TEXT, last_seen_at TEXT
            )
            """
        )


def _insert_project(path: Path, cwd: Path, *, threads: int = 4, retries: int = 1) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO derived_projects VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(cwd), str(cwd), threads, 5, retries, 20, 3, 100, 10, 25, 50, 185,
                3, "2026-01-01T00:00:00+00:00", "2026-01-02T00:00:00+00:00",
            ),
        )


def test_load_warehouse_summary_reads_current_project(tmp_path: Path) -> None:
    warehouse = tmp_path / "warehouse.db"
    project = tmp_path / "project"
    project.mkdir()
    _create_warehouse(warehouse)
    _insert_project(warehouse, project)

    summary = load_warehouse_summary(warehouse, project)

    assert summary.schema_version == 2
    assert summary.activity.threads == 4
    assert summary.activity.sessions == 5
    assert summary.activity.sessions_per_thread == 1.25
    assert summary.tokens.total_tokens == 185
    assert summary.tokens.coverage == 0.6
    assert not summary.scope.is_all_projects
    assert json.loads(render_warehouse_summary_json(summary))["tokens"]["cached_input_tokens"] == 25


def test_load_warehouse_summary_falls_back_to_all_projects(tmp_path: Path) -> None:
    warehouse = tmp_path / "warehouse.db"
    _create_warehouse(warehouse)
    _insert_project(warehouse, tmp_path / "another-project", threads=2, retries=1)

    summary = load_warehouse_summary(warehouse, tmp_path / "missing-project")

    assert summary.activity.threads == 2
    assert summary.activity.sessions == 5
    assert summary.activity.sessions_per_thread == 2.5
    assert summary.scope.is_all_projects


def test_load_warehouse_summary_resolves_worktree_to_parent(tmp_path: Path) -> None:
    warehouse = tmp_path / "warehouse.db"
    project = tmp_path / "project"
    worktree = project / ".claude" / "worktrees" / "feature"
    worktree.mkdir(parents=True)
    _create_warehouse(warehouse)
    _insert_project(warehouse, project)

    summary = load_warehouse_summary(warehouse, worktree)

    assert summary.activity.threads == 4
    assert summary.scope.project_cwd == str(project)
    assert not summary.scope.is_all_projects


def test_load_warehouse_summary_requires_derived_data(tmp_path: Path) -> None:
    warehouse = tmp_path / "warehouse.db"
    sqlite3.connect(warehouse).close()

    with pytest.raises(ValueError, match="run history-update first"):
        load_warehouse_summary(warehouse, tmp_path)
