"""Tests for typed warehouse token breakdowns."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from ai_agents_metrics.history.breakdown import (
    load_warehouse_breakdown,
    render_warehouse_breakdown,
)
from ai_agents_metrics.history.summary import load_warehouse_summary
from ai_agents_metrics.warehouse.application import BreakdownDimension


def _create_warehouse(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE derived_projects (
                project_cwd TEXT PRIMARY KEY,
                parent_project_cwd TEXT,
                thread_count INTEGER,
                attempt_count INTEGER,
                message_count INTEGER,
                usage_event_count INTEGER,
                input_tokens INTEGER,
                cache_creation_input_tokens INTEGER,
                cached_input_tokens INTEGER,
                output_tokens INTEGER,
                total_tokens INTEGER,
                total_tokens_covered_sessions INTEGER,
                first_seen_at TEXT,
                last_seen_at TEXT
            );
            CREATE TABLE derived_goals (thread_id TEXT PRIMARY KEY, cwd TEXT);
            CREATE TABLE derived_model_usage (
                thread_id TEXT,
                model TEXT,
                input_tokens INTEGER,
                cache_creation_input_tokens INTEGER,
                cached_input_tokens INTEGER,
                output_tokens INTEGER,
                total_tokens INTEGER
            );
            CREATE TABLE derived_practice_events (thread_id TEXT);
            """
        )


def _insert_project(
    path: Path,
    *,
    cwd: str,
    parent_cwd: str,
    thread_id: str,
    model: str,
    tokens: tuple[int, int, int, int, int],
) -> None:
    input_tokens, cache_creation, cached, output, total = tokens
    with sqlite3.connect(path) as connection:
        connection.execute(
            "INSERT INTO derived_projects VALUES (?, ?, 1, 1, 1, 1, ?, ?, ?, ?, ?, 1, NULL, NULL)",
            (cwd, parent_cwd, input_tokens, cache_creation, cached, output, total),
        )
        connection.execute("INSERT INTO derived_goals VALUES (?, ?)", (thread_id, cwd))
        connection.execute(
            "INSERT INTO derived_model_usage VALUES (?, ?, ?, ?, ?, ?, ?)",
            (thread_id, model, input_tokens, cache_creation, cached, output, total),
        )


def test_model_breakdown_ranks_models_and_excludes_other_projects(tmp_path: Path) -> None:
    warehouse = tmp_path / "warehouse.db"
    _create_warehouse(warehouse)
    _insert_project(
        warehouse,
        cwd="/first",
        parent_cwd="/first",
        thread_id="first-small",
        model="small",
        tokens=(10, 0, 2, 3, 15),
    )
    _insert_project(
        warehouse,
        cwd="/first/.claude/worktrees/feature",
        parent_cwd="/first",
        thread_id="first-large",
        model="large",
        tokens=(20, 0, 4, 6, 30),
    )
    _insert_project(
        warehouse,
        cwd="/second",
        parent_cwd="/second",
        thread_id="second",
        model="foreign",
        tokens=(100, 0, 0, 0, 100),
    )

    breakdown = load_warehouse_breakdown(
        warehouse, Path("/first"), BreakdownDimension.MODEL, top=None
    )

    assert [row.key for row in breakdown.rows] == ["large", "small"]
    assert [row.total_tokens for row in breakdown.rows] == [30, 15]
    assert [row.share_of_total for row in breakdown.rows] == pytest.approx([2 / 3, 1 / 3])


def test_project_breakdown_groups_worktrees_under_parent(tmp_path: Path) -> None:
    warehouse = tmp_path / "warehouse.db"
    _create_warehouse(warehouse)
    _insert_project(
        warehouse,
        cwd="/project",
        parent_cwd="/project",
        thread_id="main",
        model="model",
        tokens=(10, 1, 2, 3, 16),
    )
    _insert_project(
        warehouse,
        cwd="/project/.claude/worktrees/feature",
        parent_cwd="/project",
        thread_id="child",
        model="model",
        tokens=(20, 2, 4, 6, 32),
    )

    breakdown = load_warehouse_breakdown(
        warehouse, tmp_path / "missing", BreakdownDimension.PROJECT, top=None
    )

    assert [(row.key, row.total_tokens) for row in breakdown.rows] == [("/project", 48)]


def test_token_type_breakdown_matches_summary_scope(tmp_path: Path) -> None:
    warehouse = tmp_path / "warehouse.db"
    project = tmp_path / "project"
    _create_warehouse(warehouse)
    _insert_project(
        warehouse,
        cwd=str(project),
        parent_cwd=str(project),
        thread_id="thread",
        model="model",
        tokens=(10, 1, 2, 3, 16),
    )

    summary = load_warehouse_summary(warehouse, project)
    breakdown = load_warehouse_breakdown(
        warehouse, project, BreakdownDimension.CATEGORY, top=None
    )

    totals = {row.key: row.total_tokens for row in breakdown.rows}
    assert totals == {
        "input": summary.tokens.input_tokens,
        "cache_creation": summary.tokens.cache_creation_input_tokens,
        "cached": summary.tokens.cached_input_tokens,
        "output": summary.tokens.output_tokens,
    }


def test_top_keeps_aggregated_other_row(tmp_path: Path) -> None:
    warehouse = tmp_path / "warehouse.db"
    _create_warehouse(warehouse)
    for index, total in enumerate((30, 20, 10)):
        _insert_project(
            warehouse,
            cwd=f"/project-{index}",
            parent_cwd=f"/project-{index}",
            thread_id=f"thread-{index}",
            model=f"model-{index}",
            tokens=(total, 0, 0, 0, total),
        )

    breakdown = load_warehouse_breakdown(
        warehouse, tmp_path / "missing", BreakdownDimension.MODEL, top=1
    )

    assert [(row.key, row.total_tokens, row.grouped_row_count) for row in breakdown.rows] == [
        ("model-0", 30, 1),
        ("other", 30, 2),
    ]
    assert [row.share_of_total for row in breakdown.rows] == pytest.approx([0.5, 0.5])


def test_top_distinguishes_real_other_key_and_counts_ranked_rows(tmp_path: Path) -> None:
    warehouse = tmp_path / "warehouse.db"
    _create_warehouse(warehouse)
    _insert_project(
        warehouse,
        cwd="/first",
        parent_cwd="/first",
        thread_id="first",
        model="other",
        tokens=(30, 0, 0, 0, 30),
    )
    for index in range(2):
        _insert_project(
            warehouse,
            cwd=f"/second-{index}",
            parent_cwd=f"/second-{index}",
            thread_id=f"second-{index}",
            model="repeated",
            tokens=(10, 0, 0, 0, 10),
        )

    breakdown = load_warehouse_breakdown(
        warehouse, tmp_path / "missing", BreakdownDimension.MODEL, top=1
    )

    assert breakdown.rows[0].key == "other"
    assert not breakdown.rows[0].is_remainder
    assert breakdown.rows[1].is_remainder
    assert breakdown.rows[1].grouped_row_count == 1
    rendered = render_warehouse_breakdown(breakdown)
    assert "other | 30" in rendered
    assert "other (1 rows) | 20" in rendered


def test_project_breakdown_falls_back_when_parent_cwd_is_null(tmp_path: Path) -> None:
    warehouse = tmp_path / "warehouse.db"
    _create_warehouse(warehouse)
    with sqlite3.connect(warehouse) as connection:
        connection.execute(
            "INSERT INTO derived_projects VALUES ('/project', NULL, 1, 1, 1, 1, "
            "10, 0, 0, 0, 10, 1, NULL, NULL)"
        )

    breakdown = load_warehouse_breakdown(
        warehouse, tmp_path / "missing", BreakdownDimension.PROJECT, top=None
    )

    assert [(row.key, row.total_tokens) for row in breakdown.rows] == [("/project", 10)]


def test_model_breakdown_ignores_rows_without_cwd(tmp_path: Path) -> None:
    warehouse = tmp_path / "warehouse.db"
    _create_warehouse(warehouse)
    with sqlite3.connect(warehouse) as connection:
        connection.execute(
            "INSERT INTO derived_projects VALUES ('/project', '/project', 1, 1, 1, 1, "
            "10, 0, 0, 0, 10, 1, NULL, NULL)"
        )
        connection.execute("INSERT INTO derived_goals VALUES ('thread', NULL)")
        connection.execute(
            "INSERT INTO derived_model_usage VALUES ('thread', 'model', 10, 0, 0, 0, 10)"
        )

    breakdown = load_warehouse_breakdown(
        warehouse, tmp_path / "missing", BreakdownDimension.MODEL, top=None
    )

    assert breakdown.rows == []


def test_breakdown_reuses_gate_for_outdated_schema(tmp_path: Path) -> None:
    warehouse = tmp_path / "warehouse.db"
    sqlite3.connect(warehouse).close()

    with pytest.raises(ValueError, match="run history-update first"):
        load_warehouse_breakdown(warehouse, tmp_path, BreakdownDimension.MODEL, top=None)


def test_token_type_rejects_top_limit(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="--top is not supported"):
        load_warehouse_breakdown(
            tmp_path / "warehouse.db",
            tmp_path,
            BreakdownDimension.CATEGORY,
            top=1,
        )
