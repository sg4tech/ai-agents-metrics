"""Concrete runtime capabilities composed for CLI command handlers.

The facade is layered into submodules by concern:
  - ``orchestration`` — path constants and history-pipeline wrappers
  - ``costs`` — usage-cost resolution and cost-audit coverage

This ``__init__`` re-exports the full public surface so ``from ai_agents_metrics
import runtime_facade`` and ``runtime_facade.X`` continue to resolve every
symbol without callers knowing about the submodule layout.
"""

from ai_agents_metrics.history.breakdown import (
    load_warehouse_breakdown,
    render_warehouse_breakdown,
    render_warehouse_breakdown_json,
)
from ai_agents_metrics.history.classify import render_classify_summary_json
from ai_agents_metrics.history.derive import render_derive_summary_json
from ai_agents_metrics.history.ingest import render_ingest_summary_json
from ai_agents_metrics.history.normalize import render_normalize_summary_json
from ai_agents_metrics.history.summary import (
    load_warehouse_summary,
    render_warehouse_summary,
    render_warehouse_summary_json,
)
from ai_agents_metrics.runtime_facade.costs import (
    resolve_usage_costs,
)
from ai_agents_metrics.runtime_facade.orchestration import (
    CLAUDE_ROOT,
    CODEX_LOGS_PATH,
    CODEX_STATE_PATH,
    RAW_WAREHOUSE_PATH,
    classify_codex_history,
    derive_codex_history,
    ingest_codex_history,
    normalize_codex_history,
    verify_public_boundary,
)
from ai_agents_metrics.runtime_facade.reporting import build_html_report
from ai_agents_metrics.storage import metrics_mutation_lock
from ai_agents_metrics.usage.pricing_runtime import (
    load_effective_pricing,
    resolve_effective_pricing_path,
)
from ai_agents_metrics.usage.resolution import (
    PRICING_JSON_PATH,
    compute_event_cost_usd,
    find_usage_thread_id,
    load_pricing,
    parse_usage_event,
    resolve_codex_session_usage_window,
    resolve_codex_usage_window,
    resolve_pricing_model_alias,
    resolve_pricing_path,
    resolve_usage_session_window,
)

__all__ = [
    "CLAUDE_ROOT",
    "CODEX_LOGS_PATH",
    "CODEX_STATE_PATH",
    "PRICING_JSON_PATH",
    "RAW_WAREHOUSE_PATH",
    "classify_codex_history",
    "build_html_report",
    "compute_event_cost_usd",
    "derive_codex_history",
    "find_usage_thread_id",
    "ingest_codex_history",
    "load_effective_pricing",
    "load_pricing",
    "load_warehouse_breakdown",
    "load_warehouse_summary",
    "metrics_mutation_lock",
    "normalize_codex_history",
    "parse_usage_event",
    "render_classify_summary_json",
    "render_derive_summary_json",
    "render_ingest_summary_json",
    "render_normalize_summary_json",
    "render_warehouse_breakdown",
    "render_warehouse_breakdown_json",
    "render_warehouse_summary",
    "render_warehouse_summary_json",
    "resolve_codex_session_usage_window",
    "resolve_codex_usage_window",
    "resolve_effective_pricing_path",
    "resolve_pricing_model_alias",
    "resolve_pricing_path",
    "resolve_usage_costs",
    "resolve_usage_session_window",
    "verify_public_boundary",
]
