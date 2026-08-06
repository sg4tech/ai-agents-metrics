"""Default paths consumed by the CLI argparse layer and orchestration facade."""
from __future__ import annotations

from pathlib import Path

REPORT_HTML_PATH = Path("reports/report.html")
CODEX_STATE_PATH = Path.home() / ".codex" / "state_5.sqlite"
CODEX_LOGS_PATH = Path.home() / ".codex" / "logs_1.sqlite"
CLAUDE_ROOT = Path.home() / ".claude"
RAW_WAREHOUSE_PATH = Path(".ai-agents-metrics/warehouse.db")
PUBLIC_BOUNDARY_RULES_PATH = Path("config/public-boundary-rules.toml")
SECURITY_RULES_PATH = Path("config/security-rules.toml")
