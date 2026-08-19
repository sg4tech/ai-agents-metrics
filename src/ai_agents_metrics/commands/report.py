"""CLI handler for rendering the warehouse-backed HTML report."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ai_agents_metrics.report.html_report import (
    TokenReportRow,
    aggregate_report_data,
    check_warehouse_state,
    render_html_report,
)

_ALL_PROJECTS_KEY = "__all_projects__"

if TYPE_CHECKING:
    from argparse import Namespace

    from ai_agents_metrics.commands._runtime import CommandRuntime


@dataclass(frozen=True)
class _WarehouseRenderRows:
    sessions: dict[str, dict[str, int]] | None = None
    tokens: list[TokenReportRow] | None = None
    practice: list[tuple[str, str, int]] | None = None


def _load_render_html_project_cwds(warehouse_path: Path) -> list[str]:
    """Return warehouse projects ordered by activity volume, then path."""
    try:
        with sqlite3.connect(warehouse_path) as conn:
            rows = conn.execute(
                "SELECT cwd FROM derived_goals "
                "WHERE cwd IS NOT NULL AND cwd != '' "
                "GROUP BY cwd ORDER BY COUNT(*) DESC, cwd"
            ).fetchall()
    except sqlite3.Error, OSError:
        return []
    return [str(row[0]) for row in rows]


def _load_render_html_warehouse_rows(warehouse_path: Path, cwd: str | None) -> _WarehouseRenderRows:
    """Read session/token/practice rows from the warehouse; return empty values on error.

    A concrete cwd scopes rows to one project; ``None`` loads the whole warehouse.
    """
    params = (cwd, cwd)
    try:
        with sqlite3.connect(warehouse_path) as conn:
            session_rows = conn.execute(
                "SELECT last_seen_at, "
                "  session_count "
                "FROM derived_goals "
                "WHERE last_seen_at IS NOT NULL AND (? IS NULL OR cwd = ?)",
                params,
            ).fetchall()
            token_rows = conn.execute(
                "SELECT dg.last_seen_at, "
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
                "WHERE dg.last_seen_at IS NOT NULL AND (? IS NULL OR dg.cwd = ?) "
                "GROUP BY dg.thread_id",
                params,
            ).fetchall()
            # Practice-event distribution, scoped to the current cwd via
            # the goals table so foreign repos' events don't bleed in.
            practice_rows = conn.execute(
                "SELECT pe.practice_name, pe.source_kind, COUNT(*) "
                "FROM derived_practice_events pe "
                "JOIN derived_goals dg ON dg.thread_id = pe.thread_id "
                "WHERE (? IS NULL OR dg.cwd = ?) "
                "GROUP BY pe.practice_name, pe.source_kind",
                params,
            ).fetchall()
    except sqlite3.Error, OSError:
        return _WarehouseRenderRows()

    by_day: dict[str, dict[str, int]] = {}
    for last_seen_at, session_count in session_rows:
        day = last_seen_at[:10]
        if day not in by_day:
            by_day[day] = {"threads": 0, "sessions": 0}
        by_day[day]["threads"] += 1
        by_day[day]["sessions"] += int(session_count or 0)
    return _WarehouseRenderRows(
        sessions=by_day,
        tokens=[TokenReportRow(*row) for row in token_rows],
        practice=list(practice_rows),
    )


def _safe_load_effective_pricing(
    cli_module: CommandRuntime,
) -> dict[str, dict[str, float | None]] | None:
    try:
        return cli_module.load_effective_pricing(cwd=Path.cwd())
    except OSError, ValueError:
        return None


def _select_chart_data(
    project_reports: dict[str, dict[str, Any]], selected_project: str
) -> dict[str, Any]:
    chart_data = project_reports[selected_project].copy()
    chart_data["project_reports"] = project_reports
    chart_data["selected_project"] = selected_project
    return chart_data


def handle_render_html(args: Namespace, _cli_module: CommandRuntime) -> int:
    output_path = Path(args.output)
    cwd = getattr(args, "cwd", "") or str(Path.cwd())
    warehouse_path = Path(args.warehouse_path).expanduser()
    project_cwds = _load_render_html_project_cwds(warehouse_path)
    if cwd not in project_cwds:
        project_cwds.insert(0, cwd)
    pricing = _safe_load_effective_pricing(_cli_module)
    project_reports: dict[str, dict[str, Any]] = {}
    selected_rows = _WarehouseRenderRows()
    selected_state = check_warehouse_state(warehouse_path, cwd)
    all_rows = _load_render_html_warehouse_rows(warehouse_path, None)
    project_reports[_ALL_PROJECTS_KEY] = aggregate_report_data(
        days=args.days,
        warehouse_sessions=all_rows.sessions or {},
        warehouse_tokens=all_rows.tokens or [],
        pricing=pricing,
        warehouse_practice=all_rows.practice,
        warehouse_state={"status": "ok"} if project_cwds else selected_state,
    )
    for project_cwd in project_cwds:
        project_state = check_warehouse_state(warehouse_path, project_cwd)
        project_rows = (
            _load_render_html_warehouse_rows(warehouse_path, project_cwd)
            if project_state.get("status") == "ok" and warehouse_path.is_file()
            else _WarehouseRenderRows()
        )
        project_reports[project_cwd] = aggregate_report_data(
            days=args.days,
            warehouse_sessions=project_rows.sessions or {},
            warehouse_tokens=project_rows.tokens or [],
            pricing=pricing,
            warehouse_practice=project_rows.practice,
            warehouse_state=project_state,
        )
        if project_cwd == cwd:
            selected_rows = project_rows
            selected_state = project_state
    chart_data = _select_chart_data(project_reports, cwd)
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
