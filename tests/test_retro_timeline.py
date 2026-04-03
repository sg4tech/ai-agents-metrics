from __future__ import annotations

import json
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from tests.test_history_ingest import run_cmd

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
ABS_SCRIPT = WORKSPACE_ROOT / "scripts" / "update_codex_metrics.py"
ABS_SRC = WORKSPACE_ROOT / "src"
SRC = WORKSPACE_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from codex_metrics.domain import default_metrics, recompute_summary
from codex_metrics.retro_timeline import build_retro_timeline_report, derive_retro_timeline


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / "scripts").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "metrics").mkdir(parents=True, exist_ok=True)
    (tmp_path / "pricing").mkdir(parents=True, exist_ok=True)

    script_target = tmp_path / "scripts" / "update_codex_metrics.py"
    script_target.write_text(ABS_SCRIPT.read_text(encoding="utf-8"), encoding="utf-8")
    shutil.copytree(ABS_SRC, tmp_path / "src")

    subprocess.run(["git", "init"], cwd=tmp_path, text=True, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "codex@example.com"], cwd=tmp_path, text=True, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Codex"], cwd=tmp_path, text=True, capture_output=True, check=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, text=True, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "baseline"], cwd=tmp_path, text=True, capture_output=True, check=True)
    return tmp_path


def _build_metrics_data() -> dict[str, object]:
    data = default_metrics()
    data["goals"] = [
        {
            "goal_id": "prod-1",
            "title": "Before exact",
            "goal_type": "product",
            "supersedes_goal_id": None,
            "status": "success",
            "attempts": 1,
            "started_at": "2026-04-01T09:00:00+00:00",
            "finished_at": "2026-04-01T09:05:00+00:00",
            "cost_usd": 1.0,
            "input_tokens": None,
            "cached_input_tokens": None,
            "output_tokens": None,
            "tokens_total": 1000,
            "failure_reason": None,
            "notes": None,
            "result_fit": "exact_fit",
            "model": None,
        },
        {
            "goal_id": "prod-2",
            "title": "Before partial",
            "goal_type": "product",
            "supersedes_goal_id": None,
            "status": "success",
            "attempts": 2,
            "started_at": "2026-04-01T10:00:00+00:00",
            "finished_at": "2026-04-01T10:10:00+00:00",
            "cost_usd": 3.0,
            "input_tokens": None,
            "cached_input_tokens": None,
            "output_tokens": None,
            "tokens_total": 3000,
            "failure_reason": None,
            "notes": None,
            "result_fit": "partial_fit",
            "model": None,
        },
        {
            "goal_id": "retro-1",
            "title": "Write retro",
            "goal_type": "retro",
            "supersedes_goal_id": None,
            "status": "success",
            "attempts": 1,
            "started_at": "2026-04-01T11:00:00+00:00",
            "finished_at": "2026-04-01T11:05:00+00:00",
            "cost_usd": 0.2,
            "input_tokens": None,
            "cached_input_tokens": None,
            "output_tokens": None,
            "tokens_total": 200,
            "failure_reason": None,
            "notes": "Documented failure mode and codified follow-up",
            "result_fit": None,
            "model": None,
        },
        {
            "goal_id": "prod-3",
            "title": "After exact",
            "goal_type": "product",
            "supersedes_goal_id": None,
            "status": "success",
            "attempts": 1,
            "started_at": "2026-04-01T12:00:00+00:00",
            "finished_at": "2026-04-01T12:05:00+00:00",
            "cost_usd": 0.5,
            "input_tokens": None,
            "cached_input_tokens": None,
            "output_tokens": None,
            "tokens_total": 500,
            "failure_reason": None,
            "notes": None,
            "result_fit": "exact_fit",
            "model": None,
        },
        {
            "goal_id": "prod-4",
            "title": "After fail",
            "goal_type": "product",
            "supersedes_goal_id": None,
            "status": "fail",
            "attempts": 3,
            "started_at": "2026-04-01T13:00:00+00:00",
            "finished_at": "2026-04-01T13:20:00+00:00",
            "cost_usd": 2.0,
            "input_tokens": None,
            "cached_input_tokens": None,
            "output_tokens": None,
            "tokens_total": 2000,
            "failure_reason": "validation_failed",
            "notes": None,
            "result_fit": "miss",
            "model": None,
        },
    ]
    recompute_summary(data)
    return data


def test_build_retro_timeline_report_creates_before_after_windows(tmp_path: Path) -> None:
    metrics_path = tmp_path / "metrics" / "codex_metrics.json"
    warehouse_path = tmp_path / "metrics" / ".codex-metrics" / "retro.sqlite"
    report = build_retro_timeline_report(
        _build_metrics_data(),
        warehouse_path=warehouse_path,
        cwd=tmp_path,
        metrics_path=metrics_path,
        window_size=2,
    )

    assert len(report.events) == 1
    assert len(report.windows) == 2
    assert len(report.deltas) == 1

    record = report.records[0]
    assert record.event.goal_id == "retro-1"
    assert record.before_window.product_goals_closed == 2
    assert record.after_window.product_goals_closed == 2
    assert record.before_window.exact_fit_rate == 0.5
    assert record.after_window.exact_fit_rate == 0.5
    assert record.before_window.attempts_per_closed_product_goal == 1.5
    assert record.after_window.attempts_per_closed_product_goal == 2.0
    assert record.after_window.failure_reason_summary == '{"validation_failed": 1}'
    assert record.delta.delta_attempts_per_closed_product_goal == 0.5
    assert record.delta.delta_known_cost_per_success_usd == -1.5


def test_derive_retro_timeline_persists_sqlite_tables(tmp_path: Path) -> None:
    metrics_path = tmp_path / "metrics" / "codex_metrics.json"
    warehouse_path = tmp_path / "metrics" / ".codex-metrics" / "retro.sqlite"

    report = derive_retro_timeline(
        _build_metrics_data(),
        warehouse_path=warehouse_path,
        cwd=tmp_path,
        metrics_path=metrics_path,
        window_size=2,
    )

    assert report.warehouse_path == warehouse_path
    with sqlite3.connect(warehouse_path) as conn:
        conn.row_factory = sqlite3.Row
        assert conn.execute("SELECT count(*) FROM retro_timeline_events").fetchone()[0] == 1
        assert conn.execute("SELECT count(*) FROM retro_metric_windows").fetchone()[0] == 2
        assert conn.execute("SELECT count(*) FROM retro_window_deltas").fetchone()[0] == 1

        event = conn.execute(
            "SELECT goal_id, source_kind, title FROM retro_timeline_events WHERE retro_event_id = ?",
            ("retro-event:retro-1",),
        ).fetchone()
        assert event["goal_id"] == "retro-1"
        assert event["source_kind"] == "ledger"
        assert event["title"] == "Write retro"

        before_window = conn.execute(
            "SELECT product_goals_closed, exact_fit_rate, attempts_per_closed_product_goal FROM retro_metric_windows WHERE retro_event_id = ? AND window_side = ?",
            ("retro-event:retro-1", "before"),
        ).fetchone()
        assert before_window["product_goals_closed"] == 2
        assert before_window["exact_fit_rate"] == 0.5
        assert before_window["attempts_per_closed_product_goal"] == 1.5

        delta = conn.execute(
            "SELECT delta_attempts_per_closed_product_goal, delta_known_cost_per_success_usd FROM retro_window_deltas WHERE retro_event_id = ?",
            ("retro-event:retro-1",),
        ).fetchone()
        assert delta["delta_attempts_per_closed_product_goal"] == 0.5
        assert delta["delta_known_cost_per_success_usd"] == -1.5


def test_derive_retro_timeline_command_writes_report_and_tables(repo: Path) -> None:
    metrics_path = repo / "metrics" / "codex_metrics.json"
    warehouse_path = repo / "metrics" / ".codex-metrics" / "retro.sqlite"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(
        json.dumps(_build_metrics_data(), indent=2),
        encoding="utf-8",
    )

    result = run_cmd(
        repo,
        "derive-retro-timeline",
        "--metrics-path",
        str(metrics_path),
        "--warehouse-path",
        str(warehouse_path),
        "--window-size",
        "2",
    )

    assert result.returncode == 0, result.stderr
    assert "Retrospective Timeline Report" in result.stdout
    assert "Retro events: 1" in result.stdout
    assert "delta_attempts_per_goal: 0.5" in result.stdout

    with sqlite3.connect(warehouse_path) as conn:
        assert conn.execute("SELECT count(*) FROM retro_timeline_events").fetchone()[0] == 1
