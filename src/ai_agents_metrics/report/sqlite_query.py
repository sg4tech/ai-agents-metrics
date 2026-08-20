"""SQLite adapter for report source queries."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING, TypeAlias

from ai_agents_metrics.history.project_paths import parent_project_cwd
from ai_agents_metrics.report.application import (
    WarehouseRenderRows,
    WarehouseReportSource,
    WarehouseState,
    WarehouseStatus,
    merge_warehouse_rows,
    report_project_cwd,
)
from ai_agents_metrics.report.html_report import TokenReportRow

if TYPE_CHECKING:
    from pathlib import Path

ProjectDbRow: TypeAlias = tuple[str]
SessionDbRow: TypeAlias = tuple[str, str, int | None]
TokenDbRow: TypeAlias = tuple[str, str, str | None, str | None, int, int, int, int, int]
PracticeDbRow: TypeAlias = tuple[str, str, str, int]


class SQLiteReportQuery:
    def load_report_source(self, warehouse_path: Path) -> WarehouseReportSource:
        try:
            with sqlite3.connect(warehouse_path) as conn:
                project_rows = conn.execute(
                    "SELECT cwd FROM derived_goals WHERE cwd IS NOT NULL AND cwd != '' "
                    "GROUP BY cwd ORDER BY COUNT(*) DESC, cwd"
                ).fetchall()
                session_rows = conn.execute(
                    "SELECT cwd, last_seen_at, session_count FROM derived_goals "
                    "WHERE cwd IS NOT NULL AND cwd != '' AND last_seen_at IS NOT NULL"
                ).fetchall()
                token_rows = conn.execute(
                    "SELECT dg.cwd, dg.last_seen_at, COALESCE(dmu.model, dg.model, ("
                    "SELECT json_extract(nue.raw_json, '$.message.model') "
                    "FROM normalized_usage_events nue WHERE nue.thread_id = dg.thread_id "
                    "AND json_extract(nue.raw_json, '$.message.model') IS NOT NULL LIMIT 1)), "
                    "dg.model_provider, COALESCE(SUM(dmu.input_tokens), 0), "
                    "COALESCE(SUM(dmu.cache_creation_input_tokens), 0), "
                    "COALESCE(SUM(dmu.cached_input_tokens), 0), "
                    "COALESCE(SUM(dmu.output_tokens), 0), COALESCE(SUM(dmu.total_tokens), 0) "
                    "FROM derived_goals dg LEFT JOIN derived_model_usage dmu "
                    "ON dmu.thread_id = dg.thread_id WHERE dg.cwd IS NOT NULL AND dg.cwd != '' "
                    "AND dg.last_seen_at IS NOT NULL "
                    "GROUP BY dg.thread_id, COALESCE(dmu.model, dg.model)"
                ).fetchall()
                practice_rows = conn.execute(
                    "SELECT dg.cwd, pe.practice_name, pe.source_kind, COUNT(*) "
                    "FROM derived_practice_events pe JOIN derived_goals dg "
                    "ON dg.thread_id = pe.thread_id WHERE dg.cwd IS NOT NULL AND dg.cwd != '' "
                    "GROUP BY dg.cwd, pe.practice_name, pe.source_kind"
                ).fetchall()
        except (sqlite3.Error, OSError):
            return WarehouseReportSource()
        return _map_report_source(
            project_rows=project_rows,
            session_rows=session_rows,
            token_rows=token_rows,
            practice_rows=practice_rows,
        )

    def warehouse_state(self, warehouse_path: Path, project_cwd: str) -> WarehouseState:
        if not warehouse_path.is_file():
            return WarehouseState(WarehouseStatus.MISSING_FILE)
        try:
            with sqlite3.connect(warehouse_path) as conn:
                tables = {
                    row[0]
                    for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                }
                if not {
                    "derived_goals",
                    "derived_projects",
                    "derived_model_usage",
                    "derived_practice_events",
                } <= tables:
                    return WarehouseState(WarehouseStatus.SCHEMA_OUTDATED)
                project_columns = {
                    row[1] for row in conn.execute("PRAGMA table_info(derived_projects)")
                }
                if "parent_project_cwd" not in project_columns:
                    return WarehouseState(WarehouseStatus.SCHEMA_OUTDATED)
                canonical_cwd = parent_project_cwd(project_cwd)
                if canonical_cwd is None:
                    return WarehouseState(WarehouseStatus.EMPTY_FOR_CWD)
                count = conn.execute(
                    "SELECT COUNT(*) FROM derived_goals WHERE cwd = ?", (canonical_cwd,)
                ).fetchone()[0]
                if count == 0:
                    return WarehouseState(WarehouseStatus.EMPTY_FOR_CWD)
        except sqlite3.Error:
            return WarehouseState(WarehouseStatus.SCHEMA_OUTDATED)
        return WarehouseState.ok()


def _map_report_source(
    *,
    project_rows: list[ProjectDbRow],
    session_rows: list[SessionDbRow],
    token_rows: list[TokenDbRow],
    practice_rows: list[PracticeDbRow],
) -> WarehouseReportSource:
    """Map SQLite rows into the typed source returned by the adapter."""
    project_cwds = list(dict.fromkeys(report_project_cwd(str(row[0])) for row in project_rows))
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
        project_cwd = report_project_cwd(str(raw_cwd))
        totals = sessions_by_project[project_cwd].setdefault(
            last_seen_at[:10], {"threads": 0, "sessions": 0}
        )
        totals["threads"] += 1
        totals["sessions"] += int(session_count or 0)
    for row in token_rows:
        tokens_by_project[report_project_cwd(str(row[0]))].append(TokenReportRow(*row[1:]))
    for raw_cwd, name, kind, count in practice_rows:
        practice_by_project[report_project_cwd(str(raw_cwd))].append(
            (str(name), str(kind), int(count))
        )
    by_project = {
        project_cwd: WarehouseRenderRows(
            sessions=sessions_by_project[project_cwd],
            tokens=tokens_by_project[project_cwd],
            practice=practice_by_project[project_cwd],
        )
        for project_cwd in project_cwds
    }
    return WarehouseReportSource(
        project_cwds=project_cwds,
        by_project=by_project,
        all_projects=merge_warehouse_rows(by_project.values()),
    )
