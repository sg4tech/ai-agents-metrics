"""Tests for warehouse-only HTML report aggregation and rendering."""
from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

from ai_agents_metrics.report.html_report import (
    aggregate_report_data,
    check_warehouse_state,
    render_html_report,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_aggregate_report_data_uses_only_warehouse_rows() -> None:
    data = aggregate_report_data(
        warehouse_retry={"2026-01-01": {"threads": 4, "retry_threads": 1}},
        warehouse_tokens=[("2026-01-01T12:00:00+00:00", "gpt-test", 100, 20, 30)],
        warehouse_practice=[("Explore", "Agent", 2)],
    )
    assert data["chart1_product"] == [4]
    assert data["chart2_bar"] == [1]
    assert data["chart2_line"] == [25.0]
    assert "chart2_source" not in data
    assert "chart3_source" not in data
    assert data["chart3_series"][0]["name"] == "gpt-test"
    assert data["chart3_series"][0]["values"] == [150.0]
    assert data["chart5"]["total_events"] == 2
    assert "ledger_date_from" not in data
    assert "ledger_date_to" not in data


def test_aggregate_report_data_empty_warehouse() -> None:
    data = aggregate_report_data(warehouse_retry={}, warehouse_tokens=[])
    assert data["buckets"] == []
    assert data["summary"] is None
    assert "chart2_source" not in data


def test_aggregate_report_data_prices_known_models() -> None:
    data = aggregate_report_data(
        warehouse_retry={"2026-01-01": {"threads": 1, "retry_threads": 0}},
        warehouse_tokens=[("2026-01-01T00:00:00+00:00", "model", 1_000_000, 0, 0)],
        pricing={"model": {"input_per_million_usd": 2.0}},
    )
    assert data["chart3_mode"] == "cost"
    assert data["chart3_series"][0]["values"] == [2.0]


def test_render_html_report_embeds_warehouse_data() -> None:
    data = aggregate_report_data(
        warehouse_retry={"2026-01-01": {"threads": 1, "retry_threads": 0}},
        warehouse_tokens=[("2026-01-01T00:00:00+00:00", "model", 1, 2, 3)],
    )
    html = render_html_report(data, "2026-01-02 00:00 UTC")
    assert "<!DOCTYPE html>" in html
    assert "ledger" not in html.lower()
    assert "2026-01-02 00:00 UTC" in html


def test_check_warehouse_state_reports_missing_and_current(tmp_path: Path) -> None:
    path = tmp_path / "warehouse.db"
    assert check_warehouse_state(path, "/repo") == {"status": "missing_file"}
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE derived_goals (cwd TEXT)")
        conn.execute("CREATE TABLE derived_practice_events (practice_name TEXT)")
        conn.execute("INSERT INTO derived_goals VALUES ('/repo')")
    assert check_warehouse_state(path, "/repo") == {"status": "ok"}
