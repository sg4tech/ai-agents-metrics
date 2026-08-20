"""Warehouse-native summary queries and renderers for the ``show`` command."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING

from ai_agents_metrics.history.project_paths import parent_project_cwd

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True)
class SummaryScope:
    project_cwd: str
    is_all_projects: bool


@dataclass(frozen=True)
class ActivitySummary:
    threads: int
    sessions: int
    sessions_per_thread: float
    messages: int
    usage_events: int


@dataclass(frozen=True)
class TokenSummary:
    input_tokens: int | None
    cache_creation_input_tokens: int | None
    cached_input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None
    coverage: float | None


@dataclass(frozen=True)
class HistoryWindow:
    first_seen_at: str | None
    last_seen_at: str | None


@dataclass(frozen=True)
class WarehouseSummary:
    """Stable, agent-readable summary of derived history for one project scope."""

    schema_version: int
    scope: SummaryScope
    activity: ActivitySummary
    tokens: TokenSummary
    window: HistoryWindow


_SUMMARY_QUERY = """
        SELECT
            coalesce(sum(thread_count), 0),
            coalesce(sum(attempt_count), 0),
            coalesce(sum(message_count), 0),
            coalesce(sum(usage_event_count), 0),
            sum(input_tokens),
            sum(cache_creation_input_tokens),
            sum(cached_input_tokens),
            sum(output_tokens),
            sum(total_tokens),
            coalesce(sum(total_tokens_covered_sessions), 0),
            min(first_seen_at),
            max(last_seen_at)
        FROM derived_projects
    """
_PARENT_PROJECT_SUMMARY_QUERY = _SUMMARY_QUERY + " WHERE parent_project_cwd = ?"


def load_warehouse_summary(warehouse_path: Path, project_cwd: Path) -> WarehouseSummary:
    """Load summary data, falling back to all projects when cwd has no rows."""
    if not warehouse_path.is_file():
        raise ValueError(f"History warehouse does not exist: {warehouse_path}")

    resolved_project_cwd = parent_project_cwd(project_cwd)
    if resolved_project_cwd is None:
        raise ValueError("Project cwd must be a non-empty path")

    try:
        with sqlite3.connect(warehouse_path) as conn:
            columns = {row[1] for row in conn.execute("PRAGMA table_info(derived_projects)")}
            if "parent_project_cwd" not in columns:
                raise ValueError("History warehouse has no derived project data; run history-update first")
            row = conn.execute(
                _PARENT_PROJECT_SUMMARY_QUERY,
                (resolved_project_cwd,),
            ).fetchone()
            is_all_projects = False
            if row is None or int(row[0]) == 0:
                row = conn.execute(_SUMMARY_QUERY).fetchone()
                is_all_projects = bool(row and int(row[0]) > 0)
    except sqlite3.DatabaseError as exc:
        raise ValueError(f"Cannot read history warehouse: {exc}") from exc

    if row is None:
        raise ValueError("History warehouse has no derived project data; run history-update first")
    threads = int(row[0])
    sessions = int(row[1])
    covered_sessions = int(row[9])
    return WarehouseSummary(
        schema_version=2,
        scope=SummaryScope(
            project_cwd=resolved_project_cwd,
            is_all_projects=is_all_projects,
        ),
        activity=ActivitySummary(
            threads=threads,
            sessions=sessions,
            sessions_per_thread=(sessions / threads) if threads else 0.0,
            messages=int(row[2]), usage_events=int(row[3]),
        ),
        tokens=TokenSummary(
            input_tokens=row[4], cache_creation_input_tokens=row[5], cached_input_tokens=row[6],
            output_tokens=row[7], total_tokens=row[8],
            coverage=(covered_sessions / sessions) if sessions else None,
        ),
        window=HistoryWindow(first_seen_at=row[10], last_seen_at=row[11]),
    )


def render_warehouse_summary_json(summary: WarehouseSummary) -> str:
    return json.dumps(asdict(summary), indent=2, sort_keys=True)


def render_warehouse_summary(summary: WarehouseSummary) -> str:
    scope = "all projects (cwd had no matching history)" if summary.scope.is_all_projects else summary.scope.project_cwd
    coverage = "n/a" if summary.tokens.coverage is None else f"{summary.tokens.coverage:.2%}"
    return "\n".join(
        (
            "AI Agents Metrics — History Summary",
            f"Scope: {scope}",
            f"Threads: {summary.activity.threads}",
            f"Sessions: {summary.activity.sessions}",
            f"Sessions per thread: {summary.activity.sessions_per_thread:.2f}",
            f"Messages: {summary.activity.messages}",
            f"Tokens: total={summary.tokens.total_tokens or 0}, output={summary.tokens.output_tokens or 0}",
            f"Cache activity: read={summary.tokens.cached_input_tokens or 0}, "
            f"created={summary.tokens.cache_creation_input_tokens or 0}",
            f"Token coverage: {coverage}",
            f"History window: {summary.window.first_seen_at or 'n/a'} — {summary.window.last_seen_at or 'n/a'}",
        )
    )
