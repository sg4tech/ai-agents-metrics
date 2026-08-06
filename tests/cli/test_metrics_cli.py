"""Tests for the history-only command-line surface."""
from __future__ import annotations

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
}


def _command_choices() -> set[str]:
    parser = build_parser()
    subparsers_action = next(action for action in parser._actions if action.dest == "command")
    return set(subparsers_action.choices)


def test_manual_tracking_commands_are_removed() -> None:
    assert REMOVED_MANUAL_COMMANDS.isdisjoint(_command_choices())


def test_primary_history_commands_remain_available() -> None:
    assert {"history-update", "show", "render-html"} <= _command_choices()


def test_help_describes_history_only_workflow(capsys) -> None:
    build_parser().print_help()
    help_text = capsys.readouterr().out
    assert "history-update" in help_text
    assert "start-task" not in help_text
    assert "Manual tracking" not in help_text
