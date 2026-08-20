"""CLI handler for rendering the warehouse-backed HTML report."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeAlias

from ai_agents_metrics.history.project_paths import parent_project_cwd
from ai_agents_metrics.report.html_report import (
    TokenReportRow,
    aggregate_report_data,
    check_warehouse_state,
    render_html_report,
)

_ALL_PROJECTS_KEY = "__all_projects__"

_ProjectDbRow: TypeAlias = tuple[str]
_SessionDbRow: TypeAlias = tuple[str, str, int | None]
_TokenDbRow: TypeAlias = tuple[str, str, str | None, str | None, int, int, int, int, int]
_PracticeDbRow: TypeAlias = tuple[str, str, str, int]

if TYPE_CHECKING:
    from argparse import Namespace
    from collections.abc import Iterable

    from ai_agents_metrics.commands._runtime import CommandRuntime


@dataclass(frozen=True)
class _WarehouseRenderRows:
    sessions: dict[str, dict[str, int]] = field(default_factory=dict)
    tokens: list[TokenReportRow] = field(default_factory=list)
    practice: list[tuple[str, str, int]] = field(default_factory=list)


@dataclass(frozen=True)
class _WarehouseReportRows:
    project_cwds: list[str] = field(default_factory=list)
    by_project: dict[str, _WarehouseRenderRows] = field(default_factory=dict)
    all_projects: _WarehouseRenderRows = field(default_factory=_WarehouseRenderRows)


def _load_render_html_warehouse_rows(warehouse_path: Path) -> _WarehouseReportRows:
    """Load all report rows in one warehouse connection and group them by project."""
    try:
        with sqlite3.connect(warehouse_path) as conn:
            project_rows = conn.execute(
                "SELECT cwd FROM derived_goals WHERE cwd IS NOT NULL AND cwd != '' "
                "GROUP BY cwd ORDER BY COUNT(*) DESC, cwd"
            ).fetchall()
            session_rows = conn.execute(
                "SELECT cwd, last_seen_at, "
                "  session_count "
                "FROM derived_goals "
                "WHERE cwd IS NOT NULL AND cwd != '' AND last_seen_at IS NOT NULL",
            ).fetchall()
            token_rows = conn.execute(
                "SELECT dg.cwd, dg.last_seen_at, "
                "  COALESCE(dg.model, ("
                "    SELECT json_extract(nue.raw_json, '$.message.model') "
                "    FROM normalized_usage_events nue "
                "    WHERE nue.thread_id = dg.thread_id "
                "      AND json_extract(nue.raw_json, '$.message.model') IS NOT NULL "
                "    LIMIT 1"
                "  )) as model, "
                "  dg.model_provider, "
                "  COALESCE(SUM(dsu.input_tokens), 0), "
                "  COALESCE(SUM(dsu.cache_creation_input_tokens), 0), "
                "  COALESCE(SUM(dsu.cached_input_tokens), 0), "
                "  COALESCE(SUM(dsu.output_tokens), 0), "
                "  COALESCE(SUM(dsu.total_tokens), 0) "
                "FROM derived_goals dg "
                "LEFT JOIN derived_session_usage dsu ON dsu.thread_id = dg.thread_id "
                "WHERE dg.cwd IS NOT NULL AND dg.cwd != '' AND dg.last_seen_at IS NOT NULL "
                "GROUP BY dg.thread_id",
            ).fetchall()
            practice_rows = conn.execute(
                "SELECT dg.cwd, pe.practice_name, pe.source_kind, COUNT(*) "
                "FROM derived_practice_events pe "
                "JOIN derived_goals dg ON dg.thread_id = pe.thread_id "
                "WHERE dg.cwd IS NOT NULL AND dg.cwd != '' "
                "GROUP BY dg.cwd, pe.practice_name, pe.source_kind",
            ).fetchall()
    except (sqlite3.Error, OSError):
        return _WarehouseReportRows()

    return _build_warehouse_report_rows(
        project_rows=project_rows,
        session_rows=session_rows,
        token_rows=token_rows,
        practice_rows=practice_rows,
    )


def _build_warehouse_report_rows(
    *,
    project_rows: list[_ProjectDbRow],
    session_rows: list[_SessionDbRow],
    token_rows: list[_TokenDbRow],
    practice_rows: list[_PracticeDbRow],
) -> _WarehouseReportRows:
    """Normalize raw SQLite rows into typed per-project report inputs."""

    project_cwds = list(
        dict.fromkeys(_report_project_cwd(str(row[0])) for row in project_rows)
    )
    sessions_by_project: dict[str, dict[str, dict[str, int]]] = {
        project_cwd: {} for project_cwd in project_cwds
    }
    tokens_by_project: dict[str, list[TokenReportRow]] = {
        project_cwd: [] for project_cwd in project_cwds
    }
    practice_by_project: dict[str, list[tuple[str, str, int]]] = {
        project_cwd: [] for project_cwd in project_cwds
    }
    for raw_cwd, last_seen_at, session_count in session_rows:
        project_cwd = _report_project_cwd(str(raw_cwd))
        by_day = sessions_by_project[project_cwd]
        day = last_seen_at[:10]
        if day not in by_day:
            by_day[day] = {"threads": 0, "sessions": 0}
        by_day[day]["threads"] += 1
        by_day[day]["sessions"] += int(session_count or 0)
    for row in token_rows:
        project_cwd = _report_project_cwd(str(row[0]))
        tokens_by_project[project_cwd].append(TokenReportRow(*row[1:]))
    for raw_cwd, name, kind, count in practice_rows:
        project_cwd = _report_project_cwd(str(raw_cwd))
        practice_by_project[project_cwd].append((str(name), str(kind), int(count)))
    by_project = {
        project_cwd: _WarehouseRenderRows(
            sessions=sessions_by_project[project_cwd],
            tokens=tokens_by_project[project_cwd],
            practice=practice_by_project[project_cwd],
        )
        for project_cwd in project_cwds
    }
    return _WarehouseReportRows(
        project_cwds=project_cwds,
        by_project=by_project,
        all_projects=_merge_warehouse_rows(by_project.values()),
    )


def _report_project_cwd(cwd: str) -> str:
    """Return the canonical report key for a checkout or agent worktree."""
    return parent_project_cwd(cwd) or cwd


def _merge_warehouse_rows(rows: Iterable[_WarehouseRenderRows]) -> _WarehouseRenderRows:
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
    return _WarehouseRenderRows(
        sessions=merged_sessions,
        tokens=merged_tokens,
        practice=[(name, kind, count) for (name, kind), count in merged_practice.items()],
    )


def _safe_load_effective_pricing(
    cli_module: CommandRuntime,
) -> dict[str, dict[str, float | None]] | None:
    try:
        return cli_module.load_effective_pricing(cwd=Path.cwd())
    except (OSError, ValueError):
        return None


def _select_chart_data(
    project_reports: dict[str, dict[str, Any]], selected_project: str
) -> dict[str, Any]:
    chart_data = project_reports[selected_project].copy()
    chart_data["project_reports"] = project_reports
    chart_data["selected_project"] = selected_project
    return chart_data


def _all_projects_warehouse_state(
    selected_state: dict[str, str], project_cwds: list[str]
) -> dict[str, str]:
    if selected_state.get("status") in {"missing_file", "schema_outdated"}:
        return selected_state
    return {"status": "ok" if project_cwds else "empty_for_cwd"}


def _aggregate_project_report(
    rows: _WarehouseRenderRows,
    *,
    days: int | None,
    pricing: dict[str, dict[str, float | None]] | None,
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


def handle_render_html(args: Namespace, _cli_module: CommandRuntime) -> int:
    output_path = Path(args.output)
    cwd = getattr(args, "cwd", "") or str(Path.cwd())
    selected_project = _report_project_cwd(cwd)
    warehouse_path = Path(args.warehouse_path).expanduser()
    warehouse_rows = _load_render_html_warehouse_rows(warehouse_path)
    project_cwds = list(warehouse_rows.project_cwds)
    warehouse_project_cwds = list(project_cwds)
    if selected_project not in project_cwds:
        project_cwds.insert(0, selected_project)
    pricing = _safe_load_effective_pricing(_cli_module)
    project_reports: dict[str, dict[str, Any]] = {}
    selected_rows = _WarehouseRenderRows()
    selected_state = check_warehouse_state(warehouse_path, cwd)
    project_reports[_ALL_PROJECTS_KEY] = _aggregate_project_report(
        warehouse_rows.all_projects,
        days=args.days,
        pricing=pricing,
        state=_all_projects_warehouse_state(selected_state, warehouse_project_cwds),
    )
    for project_cwd in project_cwds:
        project_state = selected_state if project_cwd == selected_project else {"status": "ok"}
        project_rows = warehouse_rows.by_project.get(project_cwd, _WarehouseRenderRows())
        project_reports[project_cwd] = _aggregate_project_report(
            project_rows,
            days=args.days,
            pricing=pricing,
            state=project_state,
        )
        if project_cwd == selected_project:
            selected_rows = project_rows
            selected_state = project_state
    chart_data = _select_chart_data(project_reports, selected_project)
    html = render_html_report(chart_data, datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M UTC"))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(
        _render_html_source_message(
            output_path,
            warehouse_practice=selected_rows.practice,
            warehouse_state=selected_state,
        )
    )
    return 0


def _render_html_source_message(
    output_path: Path,
    *,
    warehouse_practice: list[tuple[str, str, int]] | None,
    warehouse_state: dict[str, str],
) -> str:
    practice_n = sum(c for _, _, c in warehouse_practice) if warehouse_practice else 0
    practice_src = f"warehouse ({practice_n} events)" if warehouse_practice else "none"
    wh_status = warehouse_state.get("status", "ok")
    return (
        f"Rendered HTML report: {output_path} "
        f"(sessions: warehouse, tokens: warehouse, practice: {practice_src}, "
        f"warehouse: {wh_status})"
    )
