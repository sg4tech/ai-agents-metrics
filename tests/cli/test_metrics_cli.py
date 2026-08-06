"""Tests for the history-only command-line surface."""
from __future__ import annotations

from pathlib import Path

from ai_agents_metrics import runtime_facade
from ai_agents_metrics.cli_parsers import build_parser

REMOVED_MANUAL_COMMANDS = {
    "init",
    "bootstrap",
    "start-task",
    "continue-task",
    "finish-task",
    "update",
    "ensure-active-task",
    "sync-usage",
    "sync-codex-usage",
    "merge-tasks",
    "render-report",
    "history-audit",
    "history-compare",
    "audit-cost-coverage",
    "derive-retro-timeline",
}


def _command_choices() -> set[str]:
    parser = build_parser()
    subparsers_action = next(action for action in parser._actions if action.dest == "command")
    return set(subparsers_action.choices)


def test_manual_tracking_commands_are_removed() -> None:
    assert REMOVED_MANUAL_COMMANDS.isdisjoint(_command_choices())
    assert not hasattr(runtime_facade, "bootstrap_project")


def test_primary_history_commands_remain_available() -> None:
    assert {"history-update", "show", "render-html"} <= _command_choices()


def test_help_describes_history_only_workflow(capsys) -> None:
    build_parser().print_help()
    help_text = capsys.readouterr().out
    assert "history-update" in help_text
    assert "start-task" not in help_text
    assert "Manual tracking" not in help_text


def test_maintained_docs_do_not_recommend_removed_commands() -> None:
    repo_root = Path(__file__).parents[2]
    maintained_docs = (
        "docs/architecture.md",
        "docs/architecture/README.md",
        "docs/history-pipeline.md",
        "docs/testing-guide.md",
        "docs/product-framing.md",
    )
    removed_invocations = {f"`{command}`" for command in REMOVED_MANUAL_COMMANDS}
    removed_invocations.update(f"ai-agents-metrics {command}" for command in REMOVED_MANUAL_COMMANDS)

    for relative_path in maintained_docs:
        contents = (repo_root / relative_path).read_text(encoding="utf-8")
        stale_references = sorted(reference for reference in removed_invocations if reference in contents)
        assert not stale_references, f"{relative_path} references removed commands: {stale_references}"
