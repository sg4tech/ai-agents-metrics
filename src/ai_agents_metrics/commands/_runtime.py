"""Narrow runtime protocols used by CLI command handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from contextlib import AbstractContextManager
    from pathlib import Path

    from ai_agents_metrics.history.classify import ClassifySummary
    from ai_agents_metrics.history.derive import DeriveSummary
    from ai_agents_metrics.history.ingest import IngestSummary
    from ai_agents_metrics.history.normalize import NormalizeSummary
    from ai_agents_metrics.history.summary import WarehouseSummary
    from ai_agents_metrics.public_boundary import PublicBoundaryReport
    from ai_agents_metrics.report.application import BuildReportRequest, ReportDocument
    from ai_agents_metrics.warehouse.application import WarehouseBreakdown
    from ai_agents_metrics.warehouse.domain import BreakdownDimension


class MutationLockRuntime(Protocol):
    def metrics_mutation_lock(self, path: Path) -> AbstractContextManager[None]: ...


class HistoryIngestRuntime(MutationLockRuntime, Protocol):
    def ingest_codex_history(
        self, source_root: Path, warehouse_path: Path, source: str = ...
    ) -> IngestSummary: ...
    def render_ingest_summary_json(self, summary: IngestSummary) -> str: ...


class HistoryNormalizeRuntime(MutationLockRuntime, Protocol):
    def normalize_codex_history(self, warehouse_path: Path) -> NormalizeSummary: ...
    def render_normalize_summary_json(self, summary: NormalizeSummary) -> str: ...


class HistoryClassifyRuntime(MutationLockRuntime, Protocol):
    def classify_codex_history(self, warehouse_path: Path) -> ClassifySummary: ...
    def render_classify_summary_json(self, summary: ClassifySummary) -> str: ...


class HistoryDeriveRuntime(MutationLockRuntime, Protocol):
    def derive_codex_history(self, warehouse_path: Path) -> DeriveSummary: ...
    def render_derive_summary_json(self, summary: DeriveSummary) -> str: ...


class HistoryUpdateRuntime(
    HistoryIngestRuntime,
    HistoryNormalizeRuntime,
    HistoryClassifyRuntime,
    HistoryDeriveRuntime,
    Protocol,
):
    """Runtime capabilities required by the complete history pipeline."""


class ShowRuntime(Protocol):
    def load_warehouse_breakdown(
        self,
        warehouse_path: Path,
        project_cwd: Path,
        dimension: BreakdownDimension,
        top: int | None,
    ) -> WarehouseBreakdown: ...
    def render_warehouse_breakdown(self, breakdown: WarehouseBreakdown) -> str: ...
    def render_warehouse_breakdown_json(self, breakdown: WarehouseBreakdown) -> str: ...
    def load_warehouse_summary(
        self, warehouse_path: Path, project_cwd: Path
    ) -> WarehouseSummary: ...
    def render_warehouse_summary(self, summary: WarehouseSummary) -> str: ...
    def render_warehouse_summary_json(self, summary: WarehouseSummary) -> str: ...


class PublicBoundaryRuntime(Protocol):
    def verify_public_boundary(
        self, *, repo_root: Path, rules_path: Path
    ) -> PublicBoundaryReport: ...


class ReportRuntime(Protocol):
    def build_html_report(self, request: BuildReportRequest) -> ReportDocument: ...
