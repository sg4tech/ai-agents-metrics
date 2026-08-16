"""Tests for warehouse-only HTML report aggregation and rendering."""
from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

from ai_agents_metrics.report.html_report import (
    TokenReportRow,
    aggregate_report_data,
    check_warehouse_state,
    render_html_report,
)

if TYPE_CHECKING:
    from pathlib import Path


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
    assert "Goals closed" not in html
    assert "Successes" not in html
    assert "Cost per Successful Task" not in html
    assert "Avg cost / success" not in html
    assert "2026-01-02 00:00 UTC" in html


def test_check_warehouse_state_reports_missing_and_current(tmp_path: Path) -> None:
    path = tmp_path / "warehouse.db"
    assert check_warehouse_state(path, "/repo") == {"status": "missing_file"}
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE derived_goals (cwd TEXT)")
        conn.execute("CREATE TABLE derived_practice_events (practice_name TEXT)")
        conn.execute("INSERT INTO derived_goals VALUES ('/repo')")
    assert check_warehouse_state(path, "/repo") == {"status": "ok"}
