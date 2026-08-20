"""Application use case for building a warehouse-backed HTML report."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, TypeAlias

from ai_agents_metrics.history.project_paths import parent_project_cwd
from ai_agents_metrics.report.html_report import (
    TokenReportRow,
    aggregate_report_data,
    render_html_report,
)

if TYPE_CHECKING:
    from collections.abc import Iterable
    from datetime import datetime
    from pathlib import Path

ALL_PROJECTS_KEY = "__all_projects__"
Pricing: TypeAlias = dict[str, dict[str, float | None]]


@dataclass(frozen=True)
class WarehouseRenderRows:
    sessions: dict[str, dict[str, int]] = field(default_factory=dict)
    tokens: list[TokenReportRow] = field(default_factory=list)
    practice: list[tuple[str, str, int]] = field(default_factory=list)


@dataclass(frozen=True)
class WarehouseReportSource:
    project_cwds: list[str] = field(default_factory=list)
    by_project: dict[str, WarehouseRenderRows] = field(default_factory=dict)
    all_projects: WarehouseRenderRows = field(default_factory=WarehouseRenderRows)


@dataclass(frozen=True)
class BuildReportRequest:
    warehouse_path: Path
    selected_project: Path
    days: int | None
    generated_at: datetime


@dataclass(frozen=True)
class ReportSourceSummary:
    practice_event_count: int
    warehouse_status: str


@dataclass(frozen=True)
class ReportDocument:
    html: str
    source_summary: ReportSourceSummary


class ReportQuery(Protocol):
    def load_report_source(self, warehouse_path: Path) -> WarehouseReportSource: ...
    def warehouse_state(self, warehouse_path: Path, project_cwd: str) -> dict[str, str]: ...


class PricingPort(Protocol):
    def load_pricing(self, cwd: Path) -> Pricing | None: ...


class BuildHtmlReport:
    def __init__(self, report_query: ReportQuery, pricing: PricingPort) -> None:
        self._report_query = report_query
        self._pricing = pricing

    def __call__(self, request: BuildReportRequest) -> ReportDocument:
        selected_project = report_project_cwd(str(request.selected_project))
        warehouse_rows = self._report_query.load_report_source(request.warehouse_path)
        project_cwds = list(warehouse_rows.project_cwds)
        warehouse_project_cwds = list(project_cwds)
        if selected_project not in project_cwds:
            project_cwds.insert(0, selected_project)
        pricing = self._pricing.load_pricing(request.selected_project)
        selected_state = self._report_query.warehouse_state(
            request.warehouse_path, str(request.selected_project)
        )
        project_reports: dict[str, dict[str, Any]] = {
            ALL_PROJECTS_KEY: aggregate_project_report(
                warehouse_rows.all_projects,
                days=request.days,
                pricing=pricing,
                state=all_projects_warehouse_state(selected_state, warehouse_project_cwds),
            )
        }
        selected_rows = WarehouseRenderRows()
        for project_cwd in project_cwds:
            project_state = selected_state if project_cwd == selected_project else {"status": "ok"}
            project_rows = warehouse_rows.by_project.get(project_cwd, WarehouseRenderRows())
            project_reports[project_cwd] = aggregate_project_report(
                project_rows, days=request.days, pricing=pricing, state=project_state
            )
            if project_cwd == selected_project:
                selected_rows = project_rows
                selected_state = project_state
        chart_data = select_chart_data(project_reports, selected_project)
        return ReportDocument(
            html=render_html_report(
                chart_data, request.generated_at.strftime("%Y-%m-%d %H:%M UTC")
            ),
            source_summary=ReportSourceSummary(
                practice_event_count=sum(count for _, _, count in selected_rows.practice),
                warehouse_status=selected_state.get("status", "ok"),
            ),
        )


def report_project_cwd(cwd: str) -> str:
    return parent_project_cwd(cwd) or cwd


def merge_warehouse_rows(rows: Iterable[WarehouseRenderRows]) -> WarehouseRenderRows:
    merged_sessions: dict[str, dict[str, int]] = {}
    merged_tokens: list[TokenReportRow] = []
    merged_practice: dict[tuple[str, str], int] = {}
    for project_rows in rows:
        for day, values in project_rows.sessions.items():
            totals = merged_sessions.setdefault(day, {"threads": 0, "sessions": 0})
            totals["threads"] += values["threads"]
            totals["sessions"] += values["sessions"]
        merged_tokens.extend(project_rows.tokens)
        for name, kind, count in project_rows.practice:
            merged_practice[(name, kind)] = merged_practice.get((name, kind), 0) + count
    return WarehouseRenderRows(
        sessions=merged_sessions,
        tokens=merged_tokens,
        practice=[(name, kind, count) for (name, kind), count in merged_practice.items()],
    )


def select_chart_data(
    project_reports: dict[str, dict[str, Any]], selected_project: str
) -> dict[str, Any]:
    chart_data = project_reports[selected_project].copy()
    chart_data["project_reports"] = project_reports
    chart_data["selected_project"] = selected_project
    return chart_data


def all_projects_warehouse_state(
    selected_state: dict[str, str], project_cwds: list[str]
) -> dict[str, str]:
    if selected_state.get("status") in {"missing_file", "schema_outdated"}:
        return selected_state
    return {"status": "ok" if project_cwds else "empty_for_cwd"}


def aggregate_project_report(
    rows: WarehouseRenderRows,
    *,
    days: int | None,
    pricing: Pricing | None,
    state: dict[str, str],
) -> dict[str, Any]:
    report = aggregate_report_data(
        days=days,
        warehouse_sessions=rows.sessions,
        warehouse_tokens=rows.tokens,
        pricing=pricing,
        warehouse_practice=rows.practice,
        warehouse_state=state,
    )
    if report["granularity"] == "week":
        report["daily_filter_data"] = aggregate_report_data(
            days=days,
            warehouse_sessions=rows.sessions,
            warehouse_tokens=rows.tokens,
            pricing=pricing,
            warehouse_practice=rows.practice,
            warehouse_state=state,
            bucket_granularity="day",
        )
    return report
