"""CLI handlers for history summaries and public-boundary verification."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ai_agents_metrics.public_boundary import (
    render_public_boundary_report,
    render_public_boundary_report_json,
)
from ai_agents_metrics.warehouse.domain import BreakdownDimension

if TYPE_CHECKING:
    from argparse import Namespace

    from ai_agents_metrics.commands._runtime import PublicBoundaryRuntime, ShowRuntime


def handle_show(args: Namespace, cli_module: ShowRuntime) -> int:
    warehouse_path = Path(args.warehouse_path).expanduser()
    dimension = getattr(args, "by", None)
    top = getattr(args, "top", None)
    if dimension is None and top is not None:
        raise ValueError("--top requires --by")
    if dimension is not None:
        breakdown = cli_module.load_warehouse_breakdown(
            warehouse_path,
            Path.cwd(),
            BreakdownDimension(dimension),
            top,
        )
        if getattr(args, "json", False):
            print(cli_module.render_warehouse_breakdown_json(breakdown))
        else:
            print(cli_module.render_warehouse_breakdown(breakdown))
        return 0
    summary = cli_module.load_warehouse_summary(warehouse_path, Path.cwd())
    if getattr(args, "json", False):
        print(cli_module.render_warehouse_summary_json(summary))
    else:
        print(cli_module.render_warehouse_summary(summary))
    return 0


def handle_verify_public_boundary(args: Namespace, cli_module: PublicBoundaryRuntime) -> int:
    report = cli_module.verify_public_boundary(
        repo_root=Path(args.repo_root).expanduser(),
        rules_path=Path(args.rules_path).expanduser(),
    )
    if getattr(args, "json", False):
        print(render_public_boundary_report_json(report))
    else:
        print(render_public_boundary_report(report))
    return 0 if not report.findings else 1
