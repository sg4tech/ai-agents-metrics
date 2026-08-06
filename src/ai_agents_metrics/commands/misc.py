"""CLI handlers for history summaries and public-boundary verification."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ai_agents_metrics.public_boundary import (
    render_public_boundary_report,
    render_public_boundary_report_json,
)

if TYPE_CHECKING:
    from argparse import Namespace

    from ai_agents_metrics.commands._runtime import CommandRuntime


def handle_show(args: Namespace, cli_module: CommandRuntime) -> int:
    metrics_path = Path(args.metrics_path)
    _warehouse_raw = getattr(args, "warehouse_path", "")
    # Guard against the empty-string case: Path("").expanduser() resolves to Path(".")
    # which always exists and causes an unintended SQLite connect attempt.
    warehouse_path = Path(_warehouse_raw).expanduser() if _warehouse_raw else Path()
    data = cli_module.load_metrics(metrics_path)
    cli_module.recompute_summary(data)
    history_signals = cli_module.read_history_signals(warehouse_path, Path.cwd(), data)
    if getattr(args, "json", False):
        print(cli_module.render_summary_json(data, history_signals))
    else:
        cli_module.print_summary(data, history_signals)
    return 0


def handle_verify_public_boundary(args: Namespace, cli_module: CommandRuntime) -> int:
    report = cli_module.verify_public_boundary(
        repo_root=Path(args.repo_root).expanduser(),
        rules_path=Path(args.rules_path).expanduser(),
    )
    if getattr(args, "json", False):
        print(render_public_boundary_report_json(report))
    else:
        print(render_public_boundary_report(report))
    return 0 if not report.findings else 1
