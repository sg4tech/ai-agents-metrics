"""CLI handler for rendering the warehouse-backed HTML report."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from ai_agents_metrics.report.html_report import (
    aggregate_report_data,
    check_warehouse_state,
    render_html_report,
)

if TYPE_CHECKING:
    from argparse import Namespace

    from ai_agents_metrics.commands._runtime import CommandRuntime


@dataclass(frozen=True)
class _WarehouseRenderRows:
    retry: dict[str, dict[str, int]] | None = None
    tokens: list[tuple[str, str | None, int, int, int]] | None = None
    practice: list[tuple[str, str, int]] | None = None


def _load_render_html_warehouse_rows(
    warehouse_path: Path, cwd: str
) -> _WarehouseRenderRows:
    """Read retry/token/practice rows from the warehouse; return three-way Nones on error.

    The queries pin to the given cwd so cross-repo rows don't bleed in. See
    `handle_render_html` for the warehouse-only rendering.
    """
    try:
        with sqlite3.connect(warehouse_path) as conn:
            # Use main_attempt_count (H-040 classifier) to distinguish real
            # main-agent retries from subagent Task() spawns, which also
            # produce separate session JSONL files and would otherwise
            # inflate retry_count. COALESCE treats unclassified rows as
            # single-attempt (conservative — no false retry signal).
            retry_rows = conn.execute(
                "SELECT last_seen_at, "
                "  COALESCE(main_attempt_count, 1) as main_attempts "
                "FROM derived_goals "
                "WHERE cwd = ? AND last_seen_at IS NOT NULL",
                (cwd,),
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
                "  COALESCE(SUM(dsu.input_tokens), 0), "
                "  COALESCE(SUM(dsu.cached_input_tokens), 0), "
                "  COALESCE(SUM(dsu.output_tokens), 0) "
                "FROM derived_goals dg "
                "LEFT JOIN derived_session_usage dsu ON dsu.thread_id = dg.thread_id "
                "WHERE dg.cwd = ? AND dg.last_seen_at IS NOT NULL "
                "GROUP BY dg.thread_id",
                (cwd,),
            ).fetchall()
            # Practice-event distribution, scoped to the current cwd via
            # the goals table so foreign repos' events don't bleed in.
            practice_rows = conn.execute(
                "SELECT pe.practice_name, pe.source_kind, COUNT(*) "
                "FROM derived_practice_events pe "
                "JOIN derived_goals dg ON dg.thread_id = pe.thread_id "
                "WHERE dg.cwd = ? "
                "GROUP BY pe.practice_name, pe.source_kind",
                (cwd,),
            ).fetchall()
    except (sqlite3.Error, OSError):
        return _WarehouseRenderRows()

    by_day: dict[str, dict[str, int]] = {}
    for last_seen_at, main_attempts in retry_rows:
        day = last_seen_at[:10]
        if day not in by_day:
            by_day[day] = {"threads": 0, "retry_threads": 0}
        by_day[day]["threads"] += 1
        if main_attempts and main_attempts > 1:
            by_day[day]["retry_threads"] += 1
    return _WarehouseRenderRows(
        retry=by_day,
        tokens=list(token_rows),
        practice=list(practice_rows),
    )


def _safe_load_effective_pricing(
    cli_module: CommandRuntime,
) -> dict[str, dict[str, float | None]] | None:
    try:
        return cli_module.load_effective_pricing(cwd=Path.cwd())
    except (OSError, ValueError):
        return None


def handle_render_html(args: Namespace, _cli_module: CommandRuntime) -> int:
    output_path = Path(args.output)
    cwd = getattr(args, "cwd", "") or str(Path.cwd())
    warehouse_path = Path(args.warehouse_path).expanduser()
    warehouse_state = check_warehouse_state(warehouse_path, cwd)
    # Only query warehouse when it will actually yield usable rows. An empty
    # empty_for_cwd path would otherwise produce "warehouse-source" charts
    # with all-zero values, conflicting with the warehouse-only badge and
    # callout shown to the user.
    warehouse_rows = (
        _load_render_html_warehouse_rows(warehouse_path, cwd)
        if warehouse_state.get("status") == "ok" and warehouse_path.is_file()
        else _WarehouseRenderRows()
    )

    chart_data = aggregate_report_data(
        days=args.days,
        warehouse_retry=warehouse_rows.retry or {},
        warehouse_tokens=warehouse_rows.tokens or [],
        pricing=_safe_load_effective_pricing(_cli_module),
        warehouse_practice=warehouse_rows.practice,
        warehouse_state=warehouse_state,
    )
    html = render_html_report(
        chart_data, datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M UTC")
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(_render_html_source_message(
        output_path,
        warehouse_practice=warehouse_rows.practice,
        warehouse_state=warehouse_state,
    ))
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
        f"(retry: warehouse, tokens: warehouse, practice: {practice_src}, "
        f"warehouse: {wh_status})"
    )
