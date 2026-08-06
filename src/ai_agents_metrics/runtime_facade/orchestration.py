"""Path constants and history-pipeline wrappers used by CLI handlers."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ai_agents_metrics.history.classify import (
    classify_codex_history as run_classify_codex_history,
)
from ai_agents_metrics.history.derive import (
    derive_codex_history as run_derive_codex_history,
)
from ai_agents_metrics.history.ingest import (
    ingest_codex_history as run_ingest_codex_history,
)
from ai_agents_metrics.history.normalize import (
    normalize_codex_history as run_normalize_codex_history,
)
from ai_agents_metrics.public_boundary import (
    verify_public_boundary as run_verify_public_boundary,
)

if TYPE_CHECKING:
    from ai_agents_metrics.history.classify import ClassifySummary
    from ai_agents_metrics.history.derive import DeriveSummary
    from ai_agents_metrics.history.ingest import IngestSummary
    from ai_agents_metrics.history.normalize import NormalizeSummary
    from ai_agents_metrics.public_boundary import PublicBoundaryReport


CODEX_STATE_PATH = Path.home() / ".codex" / "state_5.sqlite"
CODEX_LOGS_PATH = Path.home() / ".codex" / "logs_1.sqlite"
CLAUDE_ROOT = Path.home() / ".claude"
RAW_WAREHOUSE_PATH = Path(".ai-agents-metrics/warehouse.db")


def ingest_codex_history(source_root: Path, warehouse_path: Path, source: str = "codex") -> IngestSummary:
    return run_ingest_codex_history(source_root=source_root, warehouse_path=warehouse_path, source=source)


def normalize_codex_history(warehouse_path: Path) -> NormalizeSummary:
    return run_normalize_codex_history(warehouse_path=warehouse_path)


def derive_codex_history(warehouse_path: Path) -> DeriveSummary:
    return run_derive_codex_history(warehouse_path=warehouse_path)


def classify_codex_history(warehouse_path: Path) -> ClassifySummary:
    return run_classify_codex_history(warehouse_path=warehouse_path)


def verify_public_boundary(*, repo_root: Path, rules_path: Path) -> PublicBoundaryReport:
    return run_verify_public_boundary(repo_root=repo_root, rules_path=rules_path)
