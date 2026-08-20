#!/usr/bin/env python3
"""Command-line entrypoint for history-based AI agent metrics."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ai_agents_metrics import commands, runtime_facade
from ai_agents_metrics.cli_parsers import build_parser
from ai_agents_metrics.completion import render_completion
from ai_agents_metrics.security import render_security_report
from ai_agents_metrics.security import verify_security as security

if TYPE_CHECKING:
    import argparse


def _handle_completion(args: argparse.Namespace) -> int:
    print(render_completion(build_parser(), args.shell), end="")
    return 0


def _handle_security(args: argparse.Namespace) -> int:
    report = security(
        repo_root=Path(args.repo_root).expanduser(),
        rules_path=Path(args.rules_path).expanduser(),
    )
    print(render_security_report(report))
    return 0 if not report.findings else 1


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    dispatch: dict[str, Any] = {
        "show": commands.handle_show,
        "install-self": commands.handle_install_self,
        "history-ingest": commands.handle_ingest_codex_history,
        "history-normalize": commands.handle_normalize_codex_history,
        "history-classify": commands.handle_classify_codex_history,
        "history-derive": commands.handle_derive_codex_history,
        "history-update": commands.handle_history_update,
        "verify-public-boundary": commands.handle_verify_public_boundary,
        "render-html": commands.handle_render_html,
    }
    handler = dispatch.get(args.command)
    if handler is not None:
        return int(handler(args, runtime_facade))
    if args.command == "completion":
        return _handle_completion(args)
    if args.command == "security":
        return _handle_security(args)
    parser.error("Unknown command")
    return 2


def console_main() -> int:
    try:
        return main()
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(console_main())
