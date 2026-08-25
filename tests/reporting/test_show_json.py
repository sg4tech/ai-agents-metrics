"""Tests for the warehouse-native show handler."""
from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path
from typing import TYPE_CHECKING

from ai_agents_metrics import commands
from ai_agents_metrics.history.breakdown import (
    render_warehouse_breakdown,
    render_warehouse_breakdown_json,
)
from ai_agents_metrics.history.summary import (
    ActivitySummary,
    HistoryWindow,
    SummaryScope,
    TokenSummary,
    WarehouseSummary,
    render_warehouse_summary,
    render_warehouse_summary_json,
)
from ai_agents_metrics.warehouse.application import (
    BreakdownDimension,
    BreakdownRow,
    WarehouseBreakdown,
)

if TYPE_CHECKING:
    import pytest


class _FakeRuntime:
    summary = WarehouseSummary(
        schema_version=2,
        scope=SummaryScope(project_cwd=str(Path.cwd()), is_all_projects=False),
        activity=ActivitySummary(threads=3, sessions=4, sessions_per_thread=4 / 3, messages=12, usage_events=2),
        tokens=TokenSummary(input_tokens=10, cache_creation_input_tokens=0, cached_input_tokens=5,
                            output_tokens=7, total_tokens=22, coverage=0.5),
        window=HistoryWindow(first_seen_at="2026-01-01", last_seen_at="2026-01-02"),
    )
    breakdown = WarehouseBreakdown(
        schema_version=1,
        dimension=BreakdownDimension.MODEL,
        scope=SummaryScope(project_cwd=str(Path.cwd()), is_all_projects=False),
        rows=[
            BreakdownRow(
                key="model",
                input_tokens=10,
                cache_creation_input_tokens=0,
                cached_input_tokens=5,
                output_tokens=7,
                total_tokens=22,
                share_of_total=1.0,
            )
        ],
    )

    def load_warehouse_breakdown(
        self,
        warehouse_path: Path,
        project_cwd: Path,
        dimension: BreakdownDimension,
        top: int | None,
    ) -> WarehouseBreakdown:
        assert warehouse_path == Path("/warehouse.db")
        assert dimension is BreakdownDimension.MODEL
        assert top == 1
        return self.breakdown

    def render_warehouse_breakdown_json(self, breakdown: WarehouseBreakdown) -> str:
        return render_warehouse_breakdown_json(breakdown)

    def render_warehouse_breakdown(self, breakdown: WarehouseBreakdown) -> str:
        return render_warehouse_breakdown(breakdown)

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
    assert payload["schema_version"] == 2
    assert payload["activity"]["threads"] == 3
    assert payload["activity"]["sessions"] == 4
    assert "attempts" not in payload["activity"]
    assert payload["tokens"]["total_tokens"] == 22


def test_handle_show_prints_text(capsys: pytest.CaptureFixture[str]) -> None:
    assert commands.handle_show(Namespace(json=False, warehouse_path="/warehouse.db"), _FakeRuntime()) == 0
    output = capsys.readouterr().out
    assert "Sessions: 4" in output
    assert "Sessions per thread: 1.33" in output
    assert "Attempts" not in output
    assert "Retry pressure" not in output
    assert "Usage events" not in output
    assert "Tokens: total=22, output=7" in output
    assert "Cache activity: read=5, created=0" in output
    assert "input=" not in output


def test_handle_show_prints_breakdown_json(capsys: pytest.CaptureFixture[str]) -> None:
    result = commands.handle_show(
        Namespace(
            by="model",
            top=1,
            json=True,
            warehouse_path="/warehouse.db",
        ),
        _FakeRuntime(),
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["dimension"] == "model"
    assert payload["rows"][0]["key"] == "model"
