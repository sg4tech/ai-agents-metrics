"""Tests for the warehouse-native show handler."""
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
    render_warehouse_summary,
    render_warehouse_summary_json,
)

if TYPE_CHECKING:
    import pytest


class _FakeRuntime:
    summary = WarehouseSummary(
        schema_version=1,
        scope=SummaryScope(project_cwd=str(Path.cwd()), is_all_projects=False),
        activity=ActivitySummary(threads=3, attempts=4, retry_threads=1, retry_rate=1 / 3, messages=12, usage_events=2),
        tokens=TokenSummary(input_tokens=10, cache_creation_input_tokens=0, cached_input_tokens=5,
                            output_tokens=7, total_tokens=22, coverage=0.5),
        window=HistoryWindow(first_seen_at="2026-01-01", last_seen_at="2026-01-02"),
    )

    def load_warehouse_summary(self, warehouse_path: Path, project_cwd: Path) -> WarehouseSummary:
        assert warehouse_path == Path("/warehouse.db")
        return self.summary

    def render_warehouse_summary_json(self, summary: WarehouseSummary) -> str:
        return render_warehouse_summary_json(summary)

    def render_warehouse_summary(self, summary: WarehouseSummary) -> str:
        return render_warehouse_summary(summary)


def test_handle_show_prints_json(capsys: pytest.CaptureFixture[str]) -> None:
    assert commands.handle_show(Namespace(json=True, warehouse_path="/warehouse.db"), _FakeRuntime()) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema_version"] == 1
    assert payload["activity"]["threads"] == 3
    assert payload["tokens"]["total_tokens"] == 22


def test_handle_show_prints_text(capsys: pytest.CaptureFixture[str]) -> None:
    assert commands.handle_show(Namespace(json=False, warehouse_path="/warehouse.db"), _FakeRuntime()) == 0
    assert "Retry pressure: 1/3" in capsys.readouterr().out
