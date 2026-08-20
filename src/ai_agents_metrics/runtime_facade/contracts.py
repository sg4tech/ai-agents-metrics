"""Static checks binding the concrete runtime facade to command protocols."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai_agents_metrics import runtime_facade
    from ai_agents_metrics.commands import (
        HistoryUpdateRuntime,
        PublicBoundaryRuntime,
        ReportRuntime,
        ShowRuntime,
    )

    history_runtime: HistoryUpdateRuntime = runtime_facade
    show_runtime: ShowRuntime = runtime_facade
    public_boundary_runtime: PublicBoundaryRuntime = runtime_facade
    report_runtime: ReportRuntime = runtime_facade
