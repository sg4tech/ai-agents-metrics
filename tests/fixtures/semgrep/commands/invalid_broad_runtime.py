"""Fixture containing a handler coupled to the legacy aggregate runtime."""

from ai_agents_metrics.commands import CommandRuntime


def handle_report(runtime: CommandRuntime) -> None:
    runtime.render_warehouse_summary_json  # noqa: B018
