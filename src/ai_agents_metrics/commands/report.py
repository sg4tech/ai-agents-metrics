"""CLI handler for rendering the warehouse-backed HTML report."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from ai_agents_metrics.report.application import (
    BuildReportRequest,
    ReportDocument,
    ReportSourceSummary,
)

if TYPE_CHECKING:
    from argparse import Namespace


class ReportRuntime(Protocol):
    def build_html_report(self, request: BuildReportRequest) -> ReportDocument: ...


def handle_render_html(args: Namespace, cli_module: ReportRuntime) -> int:
    output_path = Path(args.output)
    selected_project = Path(getattr(args, "cwd", "") or Path.cwd())
    document = cli_module.build_html_report(
        BuildReportRequest(
            warehouse_path=Path(args.warehouse_path).expanduser(),
            selected_project=selected_project,
            days=args.days,
            generated_at=datetime.now(tz=UTC),
        )
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(document.html, encoding="utf-8")
    print(_render_html_source_message(output_path, document.source_summary))
    return 0


def _render_html_source_message(output_path: Path, summary: ReportSourceSummary) -> str:
    practice_src = (
        f"warehouse ({summary.practice_event_count} events)"
        if summary.practice_event_count
        else "none"
    )
    return (
        f"Rendered HTML report: {output_path} "
        f"(sessions: warehouse, tokens: warehouse, practice: {practice_src}, "
        f"warehouse: {summary.warehouse_status})"
    )
