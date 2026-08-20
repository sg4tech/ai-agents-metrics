"""Generate a self-contained HTML report with four trend charts.

Public API (imported by commands.py and tests):
- :func:`aggregate_report_data` — transform warehouse rows into chart data
- :func:`render_html_report`    — serialise chart data into a standalone HTML file
- :func:`check_warehouse_state` — classify the warehouse file for the current project

All private helpers and the HTML template live in the sub-modules below.
"""
from __future__ import annotations

import json
import sqlite3
from typing import TYPE_CHECKING, Any

from ai_agents_metrics.history.project_paths import parent_project_cwd

from .aggregation import (
    TokenReportRow,
    aggregate_report_data,
)
from .template import _HTML_TEMPLATE

if TYPE_CHECKING:
    from pathlib import Path

__all__ = [
    "TokenReportRow",
    "aggregate_report_data",
    "render_html_report",
    "check_warehouse_state",
]


# Tables required by report queries. Missing report inputs must surface a
# history-update callout instead of silently producing empty charts.
_SCHEMA_FRESHNESS_TABLES = frozenset({"derived_model_usage", "derived_practice_events"})


def check_warehouse_state(warehouse_path: Path, cwd: str) -> dict[str, str]:
    """Classify the warehouse state for the current project.

    Returns one of four status dicts:
      - ``{"status": "ok"}`` — file exists, schema current, has rows for cwd
      - ``{"status": "missing_file"}`` — warehouse file not present
      - ``{"status": "schema_outdated"}`` — file present but critical table missing
      - ``{"status": "empty_for_cwd"}`` — file and schema fine but 0 rows for cwd

    The HTML template renders a callout for non-ok states with a hint to run
    ``ai-agents-metrics history-update``. This surfaces the silent fallback
    condition where warehouse-sourced charts cannot be produced.
    """
    if not warehouse_path.is_file():
        return {"status": "missing_file"}
    try:
        with sqlite3.connect(warehouse_path) as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            if not {"derived_goals", "derived_projects", *_SCHEMA_FRESHNESS_TABLES} <= tables:
                return {"status": "schema_outdated"}
            project_columns = {
                row[1] for row in conn.execute("PRAGMA table_info(derived_projects)")
            }
            if "parent_project_cwd" not in project_columns:
                return {"status": "schema_outdated"}
            project_cwd = parent_project_cwd(cwd)
            if project_cwd is None:
                return {"status": "empty_for_cwd"}
            count = conn.execute(
                "SELECT COUNT(*) FROM derived_goals WHERE cwd = ?",
                (project_cwd,),
            ).fetchone()[0]
            if count == 0:
                return {"status": "empty_for_cwd"}
    except sqlite3.Error:
        # Treat any SQL error (locked, corrupt, schema drift) as needing refresh.
        return {"status": "schema_outdated"}
    return {"status": "ok"}


def render_html_report(data: dict[str, Any], generated_at: str) -> str:
    """Return the full HTML string for the report."""
    gran = data.get("granularity", "day")
    gran_noun = "day" if gran == "day" else "week"
    granularity_label = "Daily buckets" if gran == "day" else "Weekly buckets"

    # Escape </script> sequences so JSON cannot break out of the script block.
    safe_json = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")

    return (
        _HTML_TEMPLATE
        .replace("{DATA_JSON}", safe_json)
        .replace("{GENERATED_AT}", generated_at)
        .replace("{GRANULARITY_LABEL}", granularity_label)
        .replace("{GRAN_NOUN}", gran_noun)
    )
