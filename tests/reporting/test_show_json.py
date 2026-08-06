from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path
from typing import TYPE_CHECKING

from ai_agents_metrics import commands
from ai_agents_metrics.history.summary import (
    ActivitySummary,
    HistoryWindow,
    SummaryScope,
    TokenSummary,
    WarehouseSummary,
    render_warehouse_summary_json,
)
from ai_agents_metrics.reporting import render_summary_json

if TYPE_CHECKING:
    import pytest


class _FakeRuntime:
    summary = WarehouseSummary(
        schema_version=1,
        scope=SummaryScope(project_cwd=str(Path.cwd()), is_all_projects=False),
        activity=ActivitySummary(
            threads=3, attempts=4, retry_threads=1, retry_rate=1 / 3, messages=12, usage_events=2,
        ),
        tokens=TokenSummary(
            input_tokens=10, cache_creation_input_tokens=0, cached_input_tokens=5,
            output_tokens=7, total_tokens=22, coverage=2 / 3,
        ),
        window=HistoryWindow(
            first_seen_at="2026-01-01T00:00:00+00:00",
            last_seen_at="2026-01-02T00:00:00+00:00",
        ),
    )

    def load_warehouse_summary(self, warehouse_path: Path, project_cwd: Path) -> WarehouseSummary:
        assert warehouse_path == Path("/warehouse.db")
        assert project_cwd == Path.cwd()
        return self.summary

    def render_warehouse_summary_json(self, summary: WarehouseSummary) -> str:
        return render_warehouse_summary_json(summary)


def test_render_summary_json_includes_product_quality_and_recommendations() -> None:
    data = {
        "summary": {
            "closed_tasks": 1,
            "successes": 1,
            "fails": 0,
            "total_attempts": 1,
            "total_cost_usd": 1.0,
            "total_input_tokens": 10,
            "total_cached_input_tokens": 0,
            "total_output_tokens": 20,
            "total_tokens": 30,
            "success_rate": 1.0,
            "attempts_per_closed_task": 1.0,
            "known_cost_successes": 1,
            "known_token_successes": 1,
            "known_token_breakdown_successes": 1,
            "complete_cost_successes": 1,
            "complete_token_successes": 1,
            "complete_token_breakdown_successes": 1,
            "model_summary_goals": 1,
            "model_complete_goals": 1,
            "mixed_model_goals": 0,
            "known_cost_per_success_usd": 1.0,
            "known_cost_per_success_tokens": 30.0,
            "complete_cost_per_covered_success_usd": 1.0,
            "complete_cost_per_covered_success_tokens": 30.0,
            "by_goal_type": {
                "product": {
                    "closed_tasks": 1,
                    "successes": 1,
                    "fails": 0,
                    "total_attempts": 1,
                    "total_cost_usd": 1.0,
                    "total_input_tokens": 10,
                    "total_cached_input_tokens": 0,
                    "total_output_tokens": 20,
                    "total_tokens": 30,
                    "success_rate": 1.0,
                    "attempts_per_closed_task": 1.0,
                    "known_cost_successes": 1,
                    "known_token_successes": 1,
                    "known_token_breakdown_successes": 1,
                    "complete_cost_successes": 1,
                    "complete_token_successes": 1,
                    "complete_token_breakdown_successes": 1,
                    "known_cost_per_success_usd": 1.0,
                    "known_cost_per_success_tokens": 30.0,
                    "complete_cost_per_covered_success_usd": 1.0,
                    "complete_cost_per_covered_success_tokens": 30.0,
                },
                "retro": {"closed_tasks": 0},
                "meta": {"closed_tasks": 0},
            },
            "entries": {
                "closed_entries": 1,
                "successes": 1,
                "fails": 0,
                "success_rate": 1.0,
                "total_cost_usd": 1.0,
                "total_input_tokens": 10,
                "total_cached_input_tokens": 0,
                "total_output_tokens": 20,
                "total_tokens": 30,
                "failure_reasons": {},
            },
        },
        "goals": [
            {
                "goal_id": "goal-1",
                "title": "Exact fit goal",
                "goal_type": "product",
                "supersedes_goal_id": None,
                "status": "success",
                "attempts": 1,
                "started_at": "2026-04-04T10:00:00+00:00",
                "finished_at": "2026-04-04T10:05:00+00:00",
                "cost_usd": 1.0,
                "tokens_total": 30,
                "failure_reason": None,
                "notes": None,
                "result_fit": "exact_fit",
            }
        ],
        "entries": [
            {
                "entry_id": "entry-1",
                "goal_id": "goal-1",
                "entry_type": "attempt",
                "inferred": False,
                "status": "success",
                "started_at": "2026-04-04T10:00:00+00:00",
                "finished_at": "2026-04-04T10:05:00+00:00",
                "cost_usd": 1.0,
                "input_tokens": 10,
                "cached_input_tokens": 0,
                "output_tokens": 20,
                "tokens_total": 30,
                "failure_reason": None,
                "notes": None,
            }
        ],
    }

    payload = json.loads(render_summary_json(data))
    assert payload["product_quality"]["closed_product_goals"] == 1
    assert payload["recommendations"]


def test_handle_show_prints_json(capsys: pytest.CaptureFixture[str]) -> None:
    _legacy_data = {
        "summary": {
            "closed_tasks": 1,
            "successes": 1,
            "fails": 0,
            "total_attempts": 1,
            "total_cost_usd": 1.0,
            "total_input_tokens": 10,
            "total_cached_input_tokens": 0,
            "total_output_tokens": 20,
            "total_tokens": 30,
            "success_rate": 1.0,
            "attempts_per_closed_task": 1.0,
            "known_cost_successes": 1,
            "known_token_successes": 1,
            "known_token_breakdown_successes": 1,
            "complete_cost_successes": 1,
            "complete_token_successes": 1,
            "complete_token_breakdown_successes": 1,
            "model_summary_goals": 1,
            "model_complete_goals": 1,
            "mixed_model_goals": 0,
            "known_cost_per_success_usd": 1.0,
            "known_cost_per_success_tokens": 30.0,
            "complete_cost_per_covered_success_usd": 1.0,
            "complete_cost_per_covered_success_tokens": 30.0,
            "by_goal_type": {
                "product": {
                    "closed_tasks": 1,
                    "successes": 1,
                    "fails": 0,
                    "total_attempts": 1,
                    "total_cost_usd": 1.0,
                    "total_input_tokens": 10,
                    "total_cached_input_tokens": 0,
                    "total_output_tokens": 20,
                    "total_tokens": 30,
                    "success_rate": 1.0,
                    "attempts_per_closed_task": 1.0,
                    "known_cost_successes": 1,
                    "known_token_successes": 1,
                    "known_token_breakdown_successes": 1,
                    "complete_cost_successes": 1,
                    "complete_token_successes": 1,
                    "complete_token_breakdown_successes": 1,
                    "known_cost_per_success_usd": 1.0,
                    "known_cost_per_success_tokens": 30.0,
                    "complete_cost_per_covered_success_usd": 1.0,
                    "complete_cost_per_covered_success_tokens": 30.0,
                },
                "retro": {"closed_tasks": 0},
                "meta": {"closed_tasks": 0},
            },
            "entries": {
                "closed_entries": 1,
                "successes": 1,
                "fails": 0,
                "success_rate": 1.0,
                "total_cost_usd": 1.0,
                "total_input_tokens": 10,
                "total_cached_input_tokens": 0,
                "total_output_tokens": 20,
                "total_tokens": 30,
                "failure_reasons": {},
            },
        },
        "goals": [
            {
                "goal_id": "goal-1",
                "title": "Exact fit goal",
                "goal_type": "product",
                "supersedes_goal_id": None,
                "status": "success",
                "attempts": 1,
                "started_at": "2026-04-04T10:00:00+00:00",
                "finished_at": "2026-04-04T10:05:00+00:00",
                "cost_usd": 1.0,
                "tokens_total": 30,
                "failure_reason": None,
                "notes": None,
                "result_fit": "exact_fit",
            }
        ],
        "entries": [
            {
                "entry_id": "entry-1",
                "goal_id": "goal-1",
                "entry_type": "attempt",
                "inferred": False,
                "status": "success",
                "started_at": "2026-04-04T10:00:00+00:00",
                "finished_at": "2026-04-04T10:05:00+00:00",
                "cost_usd": 1.0,
                "input_tokens": 10,
                "cached_input_tokens": 0,
                "output_tokens": 20,
                "tokens_total": 30,
                "failure_reason": None,
                "notes": None,
            }
        ],
    }
    runtime = _FakeRuntime()

    exit_code = commands.handle_show(Namespace(json=True, warehouse_path="/warehouse.db"), runtime)

    assert exit_code == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out[captured.out.index("{"):])
    assert payload["schema_version"] == 1
    assert payload["activity"]["threads"] == 3
    assert payload["tokens"]["total_tokens"] == 22


def test_render_summary_json_history_signals_present() -> None:
    from ai_agents_metrics.history.compare import HistorySignals
    from ai_agents_metrics.reporting import render_summary_json

    data = {
        "summary": {
            "closed_tasks": 0, "successes": 0, "fails": 0, "total_attempts": 0,
            "total_cost_usd": None, "total_input_tokens": None,
            "total_cached_input_tokens": None, "total_output_tokens": None,
            "total_tokens": 0, "success_rate": None, "attempts_per_closed_task": None,
            "known_cost_successes": 0, "known_token_successes": 0,
            "known_token_breakdown_successes": 0, "complete_cost_successes": 0,
            "complete_token_successes": 0, "complete_token_breakdown_successes": 0,
            "model_summary_goals": 0, "model_complete_goals": 0, "mixed_model_goals": 0,
            "known_cost_per_success_usd": None, "known_cost_per_success_tokens": None,
            "complete_cost_per_covered_success_usd": None, "complete_cost_per_covered_success_tokens": None,
            "by_goal_type": {"product": {"closed_tasks": 0}, "retro": {"closed_tasks": 0}, "meta": {"closed_tasks": 0}},
            "entries": {"closed_entries": 0, "successes": 0, "fails": 0, "success_rate": None,
                        "total_cost_usd": None, "total_input_tokens": None,
                        "total_cached_input_tokens": None, "total_output_tokens": None,
                        "total_tokens": 0, "failure_reasons": {}},
            "by_model": {},
        },
        "goals": [],
        "entries": [],
    }

    signals = HistorySignals(
        project_threads=72, retry_threads=21, retry_rate=0.29,
        ledger_goal_alignments=8, ledger_goals_total=14,
    )
    payload = json.loads(render_summary_json(data, signals))
    hs = payload["history_signals"]
    assert hs is not None
    assert hs["scope"] == "current_project"
    assert hs["project_threads"] == 72
    assert hs["retry_threads"] == 21
    assert abs(hs["retry_rate"] - 0.29) < 0.001
    assert hs["ledger_goal_alignments"] == 8
    assert hs["ledger_goals_total"] == 14


def test_render_summary_json_history_signals_all_projects_scope() -> None:
    from ai_agents_metrics.history.compare import HistorySignals
    from ai_agents_metrics.reporting import render_summary_json

    data = {
        "summary": {
            "closed_tasks": 0, "successes": 0, "fails": 0, "total_attempts": 0,
            "total_cost_usd": None, "total_input_tokens": None,
            "total_cached_input_tokens": None, "total_output_tokens": None,
            "total_tokens": 0, "success_rate": None, "attempts_per_closed_task": None,
            "known_cost_successes": 0, "known_token_successes": 0,
            "known_token_breakdown_successes": 0, "complete_cost_successes": 0,
            "complete_token_successes": 0, "complete_token_breakdown_successes": 0,
            "model_summary_goals": 0, "model_complete_goals": 0, "mixed_model_goals": 0,
            "known_cost_per_success_usd": None, "known_cost_per_success_tokens": None,
            "complete_cost_per_covered_success_usd": None, "complete_cost_per_covered_success_tokens": None,
            "by_goal_type": {"product": {"closed_tasks": 0}, "retro": {"closed_tasks": 0}, "meta": {"closed_tasks": 0}},
            "entries": {"closed_entries": 0, "successes": 0, "fails": 0, "success_rate": None,
                        "total_cost_usd": None, "total_input_tokens": None,
                        "total_cached_input_tokens": None, "total_output_tokens": None,
                        "total_tokens": 0, "failure_reasons": {}},
            "by_model": {},
        },
        "goals": [],
        "entries": [],
    }

    signals = HistorySignals(
        project_threads=40, retry_threads=10, retry_rate=0.25,
        ledger_goal_alignments=0, ledger_goals_total=0,
        is_all_projects=True,
    )
    payload = json.loads(render_summary_json(data, signals))
    hs = payload["history_signals"]
    assert hs["scope"] == "all_projects"
    assert hs["project_threads"] == 40


def test_render_summary_json_history_signals_absent() -> None:
    from ai_agents_metrics.reporting import render_summary_json

    data = {
        "summary": {
            "closed_tasks": 0, "successes": 0, "fails": 0, "total_attempts": 0,
            "total_cost_usd": None, "total_input_tokens": None,
            "total_cached_input_tokens": None, "total_output_tokens": None,
            "total_tokens": 0, "success_rate": None, "attempts_per_closed_task": None,
            "known_cost_successes": 0, "known_token_successes": 0,
            "known_token_breakdown_successes": 0, "complete_cost_successes": 0,
            "complete_token_successes": 0, "complete_token_breakdown_successes": 0,
            "model_summary_goals": 0, "model_complete_goals": 0, "mixed_model_goals": 0,
            "known_cost_per_success_usd": None, "known_cost_per_success_tokens": None,
            "complete_cost_per_covered_success_usd": None, "complete_cost_per_covered_success_tokens": None,
            "by_goal_type": {"product": {"closed_tasks": 0}, "retro": {"closed_tasks": 0}, "meta": {"closed_tasks": 0}},
            "entries": {"closed_entries": 0, "successes": 0, "fails": 0, "success_rate": None,
                        "total_cost_usd": None, "total_input_tokens": None,
                        "total_cached_input_tokens": None, "total_output_tokens": None,
                        "total_tokens": 0, "failure_reasons": {}},
            "by_model": {},
        },
        "goals": [],
        "entries": [],
    }
    payload = json.loads(render_summary_json(data, None))
    assert payload["history_signals"] is None
