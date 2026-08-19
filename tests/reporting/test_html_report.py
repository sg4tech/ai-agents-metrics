"""Tests for warehouse-only HTML report aggregation and rendering."""

from __future__ import annotations

import json
import sqlite3
from typing import TYPE_CHECKING

import pytest

from ai_agents_metrics.commands.report import (
    _aggregate_project_report,
    _all_projects_warehouse_state,
    _load_render_html_warehouse_rows,
    _report_project_cwd,
    _select_chart_data,
    _WarehouseRenderRows,
)
from ai_agents_metrics.report.html_report import (
    TokenReportRow,
    aggregate_report_data,
    check_warehouse_state,
    render_html_report,
)

if TYPE_CHECKING:
    from pathlib import Path

    from pytest import MonkeyPatch


def test_aggregate_report_data_uses_only_warehouse_rows() -> None:
    data = aggregate_report_data(
        warehouse_sessions={"2026-01-01": {"threads": 4, "sessions": 5}},
        warehouse_tokens=[
            TokenReportRow(
                timestamp="2026-01-01T12:00:00+00:00",
                model="gpt-test",
                model_provider="openai",
                input_tokens=100,
                cache_creation_input_tokens=0,
                cached_input_tokens=20,
                output_tokens=30,
                total_tokens=130,
            )
        ],
        warehouse_practice=[("Explore", "Agent", 2)],
    )
    assert data["chart1_threads"] == [4]
    assert data["chart2_bar"] == [5]
    assert data["chart2_line"] == [1.25]
    assert "chart2_source" not in data
    assert "chart3_source" not in data
    assert data["chart3_series"][0]["name"] == "gpt-test"
    assert data["chart3_series"][0]["values"] == [130.0]
    assert data["chart5"]["total_events"] == 2
    assert "ledger_date_from" not in data
    assert "ledger_date_to" not in data


def test_aggregate_report_data_empty_warehouse() -> None:
    data = aggregate_report_data(warehouse_sessions={}, warehouse_tokens=[])
    assert data["buckets"] == []
    assert data["summary"] is None
    assert "chart2_source" not in data


def test_aggregate_report_data_prices_openai_cached_input_as_input_subset() -> None:
    data = aggregate_report_data(
        warehouse_sessions={"2026-01-01": {"threads": 1, "sessions": 1}},
        warehouse_tokens=[
            TokenReportRow(
                timestamp="2026-01-01T00:00:00+00:00",
                model="model",
                model_provider="openai",
                input_tokens=1_000_000,
                cache_creation_input_tokens=0,
                cached_input_tokens=250_000,
                output_tokens=0,
                total_tokens=1_000_000,
            )
        ],
        pricing={
            "model": {
                "input_per_million_usd": 2.0,
                "cached_input_per_million_usd": 0.5,
            }
        },
    )
    assert data["chart3_mode"] == "cost"
    assert data["chart3_series"][0]["values"] == [1.625]


def test_aggregate_report_data_prices_anthropic_cache_categories_separately() -> None:
    data = aggregate_report_data(
        warehouse_sessions={"2026-01-01": {"threads": 1, "sessions": 1}},
        warehouse_tokens=[
            TokenReportRow(
                timestamp="2026-01-01T00:00:00+00:00",
                model="model",
                model_provider="anthropic",
                input_tokens=1_000_000,
                cache_creation_input_tokens=100_000,
                cached_input_tokens=250_000,
                output_tokens=0,
                total_tokens=1_350_000,
            )
        ],
        pricing={
            "model": {
                "input_per_million_usd": 2.0,
                "cache_creation_per_million_usd": 2.5,
                "cached_input_per_million_usd": 0.5,
            }
        },
    )
    assert data["chart3_series"][0]["values"] == [2.375]


def test_aggregate_report_data_falls_back_to_tokens_when_model_is_unpriced() -> None:
    data = aggregate_report_data(
        warehouse_sessions={"2026-01-01": {"threads": 1, "sessions": 1}},
        warehouse_tokens=[
            TokenReportRow(
                timestamp="2026-01-01T00:00:00+00:00",
                model="unpriced-model",
                model_provider="openai",
                input_tokens=100,
                cache_creation_input_tokens=0,
                cached_input_tokens=20,
                output_tokens=30,
                total_tokens=130,
            )
        ],
        pricing={
            "another-model": {
                "input_per_million_usd": 2.0,
                "cached_input_per_million_usd": 0.5,
            }
        },
    )

    assert data["chart3_mode"] == "tokens"
    assert data["chart3_series"][0]["name"] == "unpriced-model"
    assert data["chart3_series"][0]["values"] == [130.0]


def test_aggregate_report_data_does_not_show_partial_cost_for_mixed_models() -> None:
    rows = [
        TokenReportRow(
            timestamp="2026-01-01T00:00:00+00:00",
            model=model,
            model_provider="openai",
            input_tokens=100,
            cache_creation_input_tokens=0,
            cached_input_tokens=0,
            output_tokens=0,
            total_tokens=100,
        )
        for model in ("priced-model", "unpriced-model")
    ]

    data = aggregate_report_data(
        warehouse_sessions={"2026-01-01": {"threads": 1, "sessions": 1}},
        warehouse_tokens=rows,
        pricing={
            "priced-model": {
                "input_per_million_usd": 2.0,
                "cached_input_per_million_usd": 0.5,
            }
        },
    )

    assert data["chart3_mode"] == "tokens"
    assert {series["name"] for series in data["chart3_series"]} == {
        "priced-model",
        "unpriced-model",
    }


def test_render_html_report_embeds_warehouse_data() -> None:
    data = aggregate_report_data(
        warehouse_sessions={"2026-01-01": {"threads": 1, "sessions": 1}},
        warehouse_tokens=[
            TokenReportRow(
                timestamp="2026-01-01T00:00:00+00:00",
                model="model",
                model_provider="openai",
                input_tokens=1,
                cache_creation_input_tokens=0,
                cached_input_tokens=0,
                output_tokens=2,
                total_tokens=3,
            )
        ],
    )
    html = render_html_report(data, "2026-01-02 00:00 UTC")
    assert "<!DOCTYPE html>" in html
    assert "ledger" not in html.lower()
    assert "Sessions per Thread" in html
    assert "Retry Pressure" not in html
    assert "main-agent retries" not in html
    assert "noRetries" not in html
    assert "fmt(val) + '%'" not in html
    assert "minmax(min(480px, 100%), 1fr)" in html
    assert "Goals closed" not in html
    assert "Successes" not in html
    assert "Cost per Successful Task" not in html
    assert "Avg cost / success" not in html
    assert "2026-01-02 00:00 UTC" in html


def test_render_html_report_includes_interactive_period_controls() -> None:
    data = aggregate_report_data(
        warehouse_sessions={
            "2025-01-01": {"threads": 1, "sessions": 1},
            "2026-01-01": {"threads": 2, "sessions": 3},
        },
        warehouse_tokens=[],
    )

    html = render_html_report(data, "2026-01-02 00:00 UTC")

    assert 'id="period-preset"' in html
    assert '<option value="all">All time</option>' in html
    assert '<option value="365">Last year</option>' in html
    assert 'id="period-from"' in html
    assert 'id="period-to"' in html
    assert "function applyPeriodFilter()" in html
    assert "PROJECT_DATA.daily_filter_data" in html


def test_project_report_preserves_daily_data_for_exact_period_filtering() -> None:
    rows = _WarehouseRenderRows(
        sessions={
            "2026-01-01": {"threads": 1, "sessions": 1},
            "2026-03-01": {"threads": 2, "sessions": 3},
        }
    )

    report = _aggregate_project_report(
        rows,
        days=None,
        pricing=None,
        state={"status": "ok"},
    )

    daily = report["daily_filter_data"]
    assert report["granularity"] == "week"
    assert daily["granularity"] == "day"
    assert daily["history_date_from"] == "2026-01-01"
    assert daily["history_date_to"] == "2026-03-01"
    assert sum(daily["chart1_threads"]) == 3


def test_render_html_report_includes_project_selector() -> None:
    first = aggregate_report_data(
        warehouse_sessions={"2025-01-01": {"threads": 1, "sessions": 1}},
        warehouse_tokens=[],
    )
    second = aggregate_report_data(
        warehouse_sessions={"2026-01-01": {"threads": 2, "sessions": 3}},
        warehouse_tokens=[],
    )
    first["project_reports"] = {"/projects/first": first.copy(), "/projects/second": second}
    first["selected_project"] = "/projects/first"

    html = render_html_report(first, "2026-01-02 00:00 UTC")

    assert 'id="project-select"' in html
    assert "function applyProjectSelection()" in html
    assert "'All projects'" in html
    assert '"/projects/second"' in html


def test_load_render_html_warehouse_rows_groups_projects_and_all_projects(
    tmp_path: Path,
) -> None:
    warehouse = tmp_path / "warehouse.db"
    with sqlite3.connect(warehouse) as conn:
        conn.execute(
            "CREATE TABLE derived_goals ("
            "thread_id TEXT, cwd TEXT, last_seen_at TEXT, session_count INTEGER, "
            "model TEXT, model_provider TEXT)"
        )
        conn.execute("CREATE TABLE normalized_usage_events (thread_id TEXT, raw_json TEXT)")
        conn.execute(
            "CREATE TABLE derived_session_usage ("
            "thread_id TEXT, input_tokens INTEGER, cache_creation_input_tokens INTEGER, "
            "cached_input_tokens INTEGER, output_tokens INTEGER, total_tokens INTEGER)"
        )
        conn.execute(
            "CREATE TABLE derived_practice_events ("
            "thread_id TEXT, practice_name TEXT, source_kind TEXT)"
        )
        conn.executemany(
            "INSERT INTO derived_goals VALUES (?, ?, ?, ?, ?, ?)",
            [
                ("one", "/projects/first", "2026-01-01", 1, "model", "openai"),
                ("two", "/projects/second", "2026-01-02", 2, "model", "openai"),
                ("three", "/projects/second", "2026-01-02", 3, "model", "openai"),
            ],
        )
        conn.executemany(
            "INSERT INTO derived_session_usage VALUES (?, ?, ?, ?, ?, ?)",
            [
                ("one", 10, 0, 2, 3, 15),
                ("two", 20, 0, 4, 6, 30),
            ],
        )
        conn.executemany(
            "INSERT INTO derived_practice_events VALUES (?, ?, ?)",
            [("one", "Explore", "Agent"), ("two", "Explore", "Agent")],
        )

    rows = _load_render_html_warehouse_rows(warehouse)

    assert rows.project_cwds == [
        "/projects/second",
        "/projects/first",
    ]
    assert rows.by_project["/projects/second"].sessions["2026-01-02"] == {
        "threads": 2,
        "sessions": 5,
    }
    assert rows.all_projects.sessions == {
        "2026-01-01": {"threads": 1, "sessions": 1},
        "2026-01-02": {"threads": 2, "sessions": 5},
    }
    assert sum(row.total_tokens for row in rows.all_projects.tokens) == 45
    assert rows.all_projects.practice == [("Explore", "Agent", 2)]


@pytest.mark.parametrize(
    ("selected_state", "projects", "expected"),
    [
        ({"status": "missing_file"}, [], {"status": "missing_file"}),
        ({"status": "schema_outdated"}, [], {"status": "schema_outdated"}),
        ({"status": "empty_for_cwd"}, ["/project"], {"status": "ok"}),
        ({"status": "empty_for_cwd"}, [], {"status": "empty_for_cwd"}),
    ],
)
def test_all_projects_warehouse_state(
    selected_state: dict[str, str], projects: list[str], expected: dict[str, str]
) -> None:
    assert _all_projects_warehouse_state(selected_state, projects) == expected


def test_select_chart_data_is_json_serializable() -> None:
    project_reports = {"/projects/first": {"buckets": ["2026-01-01"]}}

    chart_data = _select_chart_data(project_reports, "/projects/first")

    assert json.loads(json.dumps(chart_data))["selected_project"] == "/projects/first"


def test_check_warehouse_state_reports_missing_and_current(tmp_path: Path) -> None:
    path = tmp_path / "warehouse.db"
    assert check_warehouse_state(path, "/repo") == {"status": "missing_file"}
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE derived_goals (cwd TEXT)")
        conn.execute("CREATE TABLE derived_practice_events (practice_name TEXT)")
        conn.execute(
            "CREATE TABLE derived_projects (project_cwd TEXT, parent_project_cwd TEXT)"
        )
        conn.execute("INSERT INTO derived_goals VALUES ('/repo')")
    assert check_warehouse_state(path, "/repo") == {"status": "ok"}


def test_check_warehouse_state_rejects_outdated_project_schema(tmp_path: Path) -> None:
    path = tmp_path / "warehouse.db"
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE derived_goals (cwd TEXT)")
        conn.execute("CREATE TABLE derived_practice_events (practice_name TEXT)")
        conn.execute("CREATE TABLE derived_projects (project_cwd TEXT)")

    assert check_warehouse_state(path, "/repo") == {"status": "schema_outdated"}


def test_check_warehouse_state_includes_child_worktree(tmp_path: Path) -> None:
    path = tmp_path / "warehouse.db"
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE derived_goals (cwd TEXT)")
        conn.execute("CREATE TABLE derived_practice_events (practice_name TEXT)")
        conn.execute(
            "CREATE TABLE derived_projects (project_cwd TEXT, parent_project_cwd TEXT)"
        )
        conn.execute("CREATE TABLE normalized_threads (cwd TEXT)")
        conn.execute("INSERT INTO derived_goals VALUES ('/repo/.claude/worktrees/feature')")
        conn.execute("INSERT INTO derived_projects VALUES ('/repo', '/repo')")
        conn.execute(
            "INSERT INTO normalized_threads VALUES ('/repo/.claude/worktrees/feature')"
        )

    assert check_warehouse_state(path, "/repo") == {"status": "ok"}


def test_load_render_html_rows_includes_child_worktree(tmp_path: Path) -> None:
    path = tmp_path / "warehouse.db"
    with sqlite3.connect(path) as conn:
        conn.executescript(
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
            CREATE TABLE derived_session_usage (
                thread_id TEXT,
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
            INSERT INTO derived_projects VALUES
                ('/repo', '/repo');
            INSERT INTO normalized_threads VALUES
                ('/repo'),
                ('/repo/.claude/worktrees/feature');
            INSERT INTO derived_goals VALUES
                ('main', '/repo', '2026-01-01T12:00:00Z', 1, 'model', 'openai'),
                ('child', '/repo/.claude/worktrees/feature', '2026-01-02T12:00:00Z', 2,
                 'model', 'openai');
            INSERT INTO derived_session_usage VALUES
                ('main', 10, 0, 0, 1, 11),
                ('child', 20, 0, 0, 2, 22);
            """
        )

    rows = _load_render_html_warehouse_rows(path)
    project_rows = rows.by_project["/repo"]

    assert rows.project_cwds == ["/repo"]
    assert project_rows.sessions == {
        "2026-01-01": {"threads": 1, "sessions": 1},
        "2026-01-02": {"threads": 1, "sessions": 2},
    }
    assert sum(row.total_tokens for row in project_rows.tokens) == 33


def test_load_render_html_rows_resolves_relative_cwd(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    path = tmp_path / "warehouse.db"
    with sqlite3.connect(path) as conn:
        conn.executescript(
            """
            CREATE TABLE normalized_threads (cwd TEXT);
            CREATE TABLE derived_goals (
                thread_id TEXT, cwd TEXT, last_seen_at TEXT, session_count INTEGER,
                model TEXT, model_provider TEXT
            );
            CREATE TABLE derived_session_usage (
                thread_id TEXT, input_tokens INTEGER,
                cache_creation_input_tokens INTEGER, cached_input_tokens INTEGER,
                output_tokens INTEGER, total_tokens INTEGER
            );
            CREATE TABLE normalized_usage_events (thread_id TEXT, raw_json TEXT);
            CREATE TABLE derived_practice_events (
                thread_id TEXT, practice_name TEXT, source_kind TEXT
            );
            """
        )
        conn.execute("INSERT INTO normalized_threads VALUES (?)", (str(project),))
        conn.execute(
            "INSERT INTO derived_goals VALUES (?, ?, ?, ?, ?, ?)",
            ("thread", str(project), "2026-01-01T12:00:00Z", 1, "model", "openai"),
        )
        conn.execute(
            "INSERT INTO derived_session_usage VALUES ('thread', 10, 0, 0, 1, 11)"
        )
    monkeypatch.chdir(project)

    rows = _load_render_html_warehouse_rows(path)

    assert _report_project_cwd(".") == str(project.resolve())
    assert rows.by_project[str(project.resolve())].sessions == {
        "2026-01-01": {"threads": 1, "sessions": 1}
    }
