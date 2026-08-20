"""Tests for report application orchestration through its ports."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from ai_agents_metrics.report.application import (
    BuildHtmlReport,
    BuildReportRequest,
    Pricing,
    ReportSourceSummary,
    WarehouseRenderRows,
    WarehouseReportSource,
    aggregate_project_report,
    all_projects_warehouse_state,
    report_project_cwd,
    select_chart_data,
)


class FakeReportQuery:
    def __init__(self, source: WarehouseReportSource, status: str = "ok") -> None:
        self.source = source
        self.status = status

    def load_report_source(self, warehouse_path: Path) -> WarehouseReportSource:
        return self.source

    def warehouse_state(self, warehouse_path: Path, project_cwd: str) -> dict[str, str]:
        return {"status": self.status}


class FakePricing:
    def load_pricing(self, cwd: Path) -> Pricing | None:
        return None


def test_build_html_report_combines_typed_sources_through_ports() -> None:
    source = WarehouseReportSource(
        project_cwds=["/project"],
        by_project={
            "/project": WarehouseRenderRows(
                sessions={"2026-08-20": {"threads": 2, "sessions": 3}},
                practice=[("Explore", "Agent", 2)],
            )
        },
    )
    use_case = BuildHtmlReport(FakeReportQuery(source), FakePricing())

    document = use_case(
        BuildReportRequest(
            warehouse_path=Path("warehouse.db"),
            selected_project=Path("/project"),
            days=30,
            generated_at=datetime(2026, 8, 20, tzinfo=UTC),
        )
    )

    assert "2026-08-20" in document.html
    assert document.source_summary == ReportSourceSummary(
        practice_event_count=2,
        warehouse_status="ok",
    )


def test_project_report_preserves_daily_data_for_exact_period_filtering() -> None:
    rows = WarehouseRenderRows(
        sessions={
            "2026-01-01": {"threads": 1, "sessions": 1},
            "2026-03-01": {"threads": 2, "sessions": 3},
        }
    )

    report = aggregate_project_report(rows, days=None, pricing=None, state={"status": "ok"})

    daily = report["daily_filter_data"]
    assert report["granularity"] == "week"
    assert daily["granularity"] == "day"
    assert daily["history_date_from"] == "2026-01-01"
    assert daily["history_date_to"] == "2026-03-01"
    assert sum(daily["chart1_threads"]) == 3


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
    assert all_projects_warehouse_state(selected_state, projects) == expected


def test_select_chart_data_is_json_serializable() -> None:
    project_reports = {"/projects/first": {"buckets": ["2026-01-01"]}}

    chart_data = select_chart_data(project_reports, "/projects/first")

    assert json.loads(json.dumps(chart_data))["selected_project"] == "/projects/first"


def test_report_project_cwd_resolves_relative_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.chdir(project)

    assert report_project_cwd(".") == str(project.resolve())
