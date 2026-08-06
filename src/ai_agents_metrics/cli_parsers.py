"""Argparse parser construction for the CLI.

Exposes ``build_parser`` plus the shared flag-/subparser-factory helpers.
Separated from ``cli.py`` so the entrypoint file stays focused on dispatch
and the facade surface used by scripts/metrics_cli.py and tests.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from ai_agents_metrics import __version__
from ai_agents_metrics.cli_constants import (
    PUBLIC_BOUNDARY_RULES_PATH,
    RAW_WAREHOUSE_PATH,
    REPORT_HTML_PATH,
    SECURITY_RULES_PATH,
)


def _detect_module_prog() -> str | None:
    """Return a human-readable prog name when invoked as ``python -m ai_agents_metrics``."""
    argv0 = sys.argv[0] if sys.argv else ""
    if Path(argv0).name == "__main__.py":
        py = f"python{sys.version_info.major}.{sys.version_info.minor}"
        return f"{py} -m ai_agents_metrics"
    return None


#: Commands that are registered and fully functional but are hidden from the
#: top-level ``--help`` subparser listing to keep the first-time user experience
#: scannable. They are still discoverable via ``<cmd> --help`` and are listed
#: by name in the parser epilog so users know they exist.
_HIDDEN_FROM_TOPLEVEL_HELP: frozenset[str] = frozenset({
    # Pipeline stages — users run the composite `history-update` instead.
    "history-ingest", "history-normalize", "history-classify", "history-derive",
    # Maintenance / low-level.
    "verify-public-boundary", "security",
})


def _add_install_parsers(subparsers: Any) -> None:
    install_self_parser = subparsers.add_parser(
        "install-self",
        help="Install this executable into ~/bin/ai-agents-metrics",
        description=(
            "Install the current ai-agents-metrics executable into a stable user-local location. "
            "On macOS/Linux this defaults to a symlink at ~/bin/ai-agents-metrics."
        ),
    )
    install_self_parser.add_argument("--target-dir", default=str(Path.home() / "bin"))
    install_self_parser.add_argument("--target-path")
    install_self_parser.add_argument("--command-name", default="ai-agents-metrics")
    install_self_parser.add_argument("--copy", action="store_true", help="Copy the executable instead of creating a symlink")
    install_self_parser.add_argument(
        "--write-shell-profile",
        action="store_true",
        help="Append the target directory to the detected shell profile when it is not already on PATH",
    )

    completion_parser = subparsers.add_parser(
        "completion",
        help="Print shell completion for bash or zsh",
        description=(
            "Print a shell completion script for ai-agents-metrics. "
            "Use this to enable command and option completion in bash or zsh."
        ),
    )
    completion_parser.add_argument("shell", choices=("bash", "zsh"))


def _add_history_parsers(subparsers: Any) -> None:
    _source_choice_help = (
        "Agent source to ingest (default: all):\n"
        "  codex   — reads ~/.codex only\n"
        "  claude  — reads ~/.claude only\n"
        "  all     — reads both ~/.codex and ~/.claude"
    )
    ingest_parser = subparsers.add_parser(
        "history-ingest",
        help="Ingest local agent history into a raw SQLite warehouse",
        description=(
            "Read thread metadata, session transcripts, telemetry events, and logs from a local "
            "agent history directory into a raw warehouse for later derivation. "
            "Supports Codex (~/.codex) and Claude Code (~/.claude)."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    ingest_parser.add_argument("--source", choices=["codex", "claude", "all"], default=None, help=_source_choice_help)
    ingest_parser.add_argument(
        "--source-root",
        default=None,
        help="Override the agent history root directory (implies --source codex unless --source is set; incompatible with --source all)",
    )
    ingest_parser.add_argument("--warehouse-path", default=str(RAW_WAREHOUSE_PATH), help="SQLite warehouse path for raw imported data")

    normalize_parser = subparsers.add_parser(
        "history-normalize",
        help="Normalize raw agent history into analysis-friendly tables",
        description=(
            "Read the raw warehouse populated by history-ingest and build normalized summary tables "
            "for downstream analysis."
        ),
    )
    normalize_parser.add_argument("--warehouse-path", default=str(RAW_WAREHOUSE_PATH), help="SQLite warehouse path that already contains raw imported data")

    classify_parser = subparsers.add_parser(
        "history-classify",
        help="Classify agent session kinds (main vs subagent) from normalized history",
        description=(
            "Read the normalized warehouse populated by history-normalize and write "
            "derived_session_kinds — a deterministic, filename-based classification of "
            "each session file as 'main' or 'subagent'. Required before history-derive "
            "to avoid subagent-aliased retry counts (see oss/docs/findings/F-001)."
        ),
    )
    classify_parser.add_argument("--warehouse-path", default=str(RAW_WAREHOUSE_PATH), help="SQLite warehouse path that already contains normalized agent history")
    classify_parser.add_argument("--json", action="store_true", default=False, help="Output summary as JSON")

    derive_parser = subparsers.add_parser(
        "history-derive",
        help="Derive analysis marts from normalized agent history",
        description=(
            "Read the normalized warehouse populated by history-normalize and build reusable "
            "analysis marts for goals, attempts, timelines, retry chains, and session usage."
        ),
    )
    derive_parser.add_argument("--warehouse-path", default=str(RAW_WAREHOUSE_PATH), help="SQLite warehouse path that already contains normalized agent history")

    history_update_parser = subparsers.add_parser(
        "history-update",
        help="Run the full history pipeline: ingest → normalize → derive",
        description=(
            "Run all three history pipeline stages in sequence: history-ingest, history-normalize, "
            "history-derive. Use this for the initial setup or to refresh the warehouse after new "
            "agent sessions. Equivalent to running the three stages separately."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    history_update_parser.add_argument("--source", choices=["codex", "claude", "all"], default=None, help=_source_choice_help)
    history_update_parser.add_argument(
        "--source-root",
        default=None,
        help="Override the agent history root directory (implies --source codex unless --source is set; incompatible with --source all)",
    )
    history_update_parser.add_argument("--warehouse-path", default=str(RAW_WAREHOUSE_PATH), help="SQLite warehouse path")
    history_update_parser.add_argument("--json", action="store_true", default=False, help="Output all three stage summaries as a single JSON object")



def _add_sync_and_render_parsers(subparsers: Any) -> None:
    show_parser = subparsers.add_parser(
        "show",
        help="Print a history-derived warehouse summary",
        description="Print retry, usage, token, and timeline metrics from the history warehouse.",
    )
    show_parser.add_argument(
        "--warehouse-path",
        default=str(RAW_WAREHOUSE_PATH),
        help="Path to the history warehouse SQLite file",
    )
    show_parser.add_argument("--json", action="store_true", help="Output summary as JSON")

    public_boundary_parser = subparsers.add_parser(
        "verify-public-boundary",
        help="Verify that a public repository tree does not contain private-only material",
        description=(
            "Check a candidate public repository tree against explicit public-boundary rules. "
            "Fail on forbidden paths, forbidden file types, unexpected roots, or private-content markers."
        ),
    )
    public_boundary_parser.add_argument("--repo-root", default=".")
    public_boundary_parser.add_argument("--rules-path", default=str(PUBLIC_BOUNDARY_RULES_PATH))

    security_parser = subparsers.add_parser(
        "security",
        help="Run a fast staged-file security scan",
        description=(
            "Scan staged changes for secrets, token patterns, private keys, and other dangerous data "
            "before it lands in git."
        ),
    )
    security_parser.add_argument("--repo-root", default=".")
    security_parser.add_argument("--rules-path", default=str(SECURITY_RULES_PATH))

    render_html_parser = subparsers.add_parser(
        "render-html",
        help="Render a self-contained HTML report with trend charts",
        description="Generate a static HTML file with four trend charts for human review.",
    )
    render_html_parser.add_argument(
        "--output",
        default=str(REPORT_HTML_PATH),
        help="Output path for the HTML file (default: reports/report.html)",
    )
    render_html_parser.add_argument("--days", type=int, default=None, metavar="N", help="Limit the time window to the last N days")
    render_html_parser.add_argument(
        "--warehouse-path", default=str(RAW_WAREHOUSE_PATH), help="SQLite warehouse path"
    )
    render_html_parser.add_argument(
        "--cwd",
        default="",
        metavar="PATH",
        help=(
            "Override the cwd used to filter warehouse rows (default: the "
            "current process cwd). Use this to query a cross-machine "
            "warehouse — e.g. --cwd /Users/viktor/PhpstormProjects/hhsave "
            "when rendering on Linux against a Mac-imported warehouse."
        ),
    )


def _hide_advanced_commands_from_help(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Drop advanced / pipeline-internal commands from the top-level `--help` listing.

    The commands remain callable and `<cmd> --help` still renders their
    per-command help. The epilog lists them by name so users know they exist.
    This mutates a private argparse attribute (stable across Py 3.9–3.13)
    because argparse has no public API to mark a subparser as hidden after
    creation.
    """
    # pylint: disable=protected-access
    subparsers._choices_actions = [  # noqa: SLF001
        act for act in subparsers._choices_actions
        if act.dest not in _HIDDEN_FROM_TOPLEVEL_HELP
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=_detect_module_prog(),
        description="Analyze your AI agent work history, track spending, and optimize your workflow. Point it at your history files and see retry pressure, token cost, and session timeline — no manual setup required.",
        epilog=(
            "Additional commands (run `<command> --help` for details):\n"
            "  History pipeline:  history-ingest, history-normalize, history-classify,\n"
            "                     history-derive\n"
            "  Maintenance:       verify-public-boundary, security\n"
            "\n"
            "Examples:\n"
            "  %(prog)s history-update\n"
            "  %(prog)s show\n"
            "  %(prog)s render-html --output /tmp/report.html\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        # A short placeholder keeps the `usage:` header readable — argparse
        # would otherwise dump all 26 choice names in a single unwrapped blob.
        metavar="<command>",
    )
    _add_install_parsers(subparsers)
    _add_history_parsers(subparsers)
    _add_sync_and_render_parsers(subparsers)
    _hide_advanced_commands_from_help(subparsers)
    return parser
