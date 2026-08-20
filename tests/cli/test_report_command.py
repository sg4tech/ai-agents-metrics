"""Tests for the HTML report command boundary."""

from __future__ import annotations

from argparse import Namespace
from datetime import UTC
from pathlib import Path

from ai_agents_metrics.commands.report import handle_render_html
from ai_agents_metrics.report.application import (
    BuildReportRequest,
    ReportDocument,
    ReportSourceSummary,
    WarehouseStatus,
)


class FakeReportRuntime:
    def __init__(self, document: ReportDocument) -> None:
        self.document = document
        self.request: BuildReportRequest | None = None

    def build_html_report(self, request: BuildReportRequest) -> ReportDocument:
        self.request = request
        return self.document


def test_render_html_handler_delegates_report_building_to_runtime(tmp_path: Path) -> None:
    output_path = tmp_path / "report.html"
    runtime = FakeReportRuntime(
        ReportDocument(
            html="<html>delegated</html>",
            source_summary=ReportSourceSummary(
                practice_event_count=3,
                warehouse_status=WarehouseStatus.OK,
            ),
        )
    )
    args = Namespace(
        output=str(output_path),
        cwd="/projects/example",
        warehouse_path=str(tmp_path / "warehouse.db"),
        days=30,
    )

    result = handle_render_html(args, runtime)

    assert result == 0
    assert output_path.read_text(encoding="utf-8") == "<html>delegated</html>"
    assert runtime.request is not None
    assert runtime.request.generated_at.tzinfo == UTC
    assert runtime.request.selected_project == Path("/projects/example")
