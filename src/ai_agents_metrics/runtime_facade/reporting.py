"""Runtime composition for HTML report generation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai_agents_metrics.report.application import (
    BuildHtmlReport,
    BuildReportRequest,
    Pricing,
    ReportDocument,
)
from ai_agents_metrics.report.sqlite_query import SQLiteReportQuery
from ai_agents_metrics.usage.pricing_runtime import load_effective_pricing

if TYPE_CHECKING:
    from pathlib import Path


class EffectivePricing:
    def load_pricing(self, cwd: Path) -> Pricing | None:
        try:
            return load_effective_pricing(cwd=cwd)
        except (OSError, ValueError):
            return None


def build_html_report(request: BuildReportRequest) -> ReportDocument:
    return BuildHtmlReport(SQLiteReportQuery(), EffectivePricing())(request)
