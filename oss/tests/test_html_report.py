"""Tests for html_report: aggregation logic and render smoke checks."""
from __future__ import annotations

from datetime import datetime

from ai_agents_metrics.html_report import (
    _bucket_key,
    _make_buckets,
    _monday_of,
    _parse_date,
    aggregate_report_data,
    render_html_report,
)

# ── helpers ───────────────────────────────────────────────────────────────────


def _goal(
    *,
    status: str = "success",
    finished_at: str | None = "2026-01-15T10:00:00+00:00",
    attempts: int = 1,
    cost_usd: float | None = None,
    input_tokens: int | None = None,
    cached_input_tokens: int | None = None,
    output_tokens: int | None = None,
    goal_type: str = "product",
) -> dict:
    return {
        "goal_id": "g1",
        "title": "T",
        "goal_type": goal_type,
        "status": status,
        "attempts": attempts,
        "finished_at": finished_at,
        "started_at": None,
        "cost_usd": cost_usd,
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_input_tokens,
        "output_tokens": output_tokens,
        "tokens_total": None,
        "failure_reason": None,
        "notes": None,
        "agent_name": None,
        "result_fit": None,
    }


# ── parse helpers ─────────────────────────────────────────────────────────────


def test_parse_date_none():
    assert _parse_date(None) is None


def test_parse_date_valid():
    dt = _parse_date("2026-01-15T10:00:00+00:00")
    assert dt is not None
    assert dt.year == 2026 and dt.month == 1 and dt.day == 15


def test_parse_date_z_suffix():
    dt = _parse_date("2026-03-01T00:00:00Z")
    assert dt is not None and dt.month == 3


def test_monday_of():
    # 2026-01-14 is a Wednesday → Monday is 2026-01-12
    dt = datetime(2026, 1, 14, 15, 30)
    monday = _monday_of(dt)
    assert monday.weekday() == 0
    assert monday.strftime("%Y-%m-%d") == "2026-01-12"


# ── bucketing ─────────────────────────────────────────────────────────────────


def test_make_buckets_daily():
    earliest = datetime(2026, 1, 1)
    latest = datetime(2026, 1, 5)
    buckets = _make_buckets(earliest, latest, "day")
    assert buckets == ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04", "2026-01-05"]


def test_make_buckets_weekly():
    earliest = datetime(2026, 1, 5)   # Monday
    latest = datetime(2026, 1, 19)    # Monday (two weeks later)
    buckets = _make_buckets(earliest, latest, "week")
    assert buckets == ["2026-01-05", "2026-01-12", "2026-01-19"]


def test_bucket_key_daily():
    dt = datetime(2026, 3, 15, 12, 0, tzinfo=None)
    assert _bucket_key(dt, "day") == "2026-03-15"


def test_bucket_key_weekly():
    # Wednesday 2026-01-14 → week of Monday 2026-01-12
    from datetime import timezone
    dt = datetime(2026, 1, 14, 9, 0, tzinfo=timezone.utc)
    assert _bucket_key(dt, "week") == "2026-01-12"


# ── aggregate_report_data ─────────────────────────────────────────────────────


def test_empty_goals_returns_empty_data():
    result = aggregate_report_data([], days=None)
    assert result["buckets"] == []
    assert result["chart1"] == []
    assert result["chart4_buckets"] == []


def test_in_progress_goals_excluded():
    goals = [_goal(status="in_progress", finished_at="2026-01-15T10:00:00+00:00")]
    result = aggregate_report_data(goals, days=None)
    assert result["buckets"] == []


def test_goals_without_finished_at_excluded():
    goals = [_goal(status="success", finished_at=None)]
    result = aggregate_report_data(goals, days=None)
    assert result["buckets"] == []


def test_single_success_daily():
    goals = [_goal(status="success", finished_at="2026-01-15T10:00:00+00:00")]
    result = aggregate_report_data(goals, days=None)
    assert "2026-01-15" in result["buckets"]
    idx = result["buckets"].index("2026-01-15")
    assert result["chart1"][idx] == 1


def test_fail_not_counted_in_chart1():
    goals = [_goal(status="fail", finished_at="2026-01-15T10:00:00+00:00")]
    result = aggregate_report_data(goals, days=None)
    assert result["chart1"][0] == 0


def test_retry_pressure_chart2():
    goals = [
        _goal(status="success", finished_at="2026-01-15T10:00:00+00:00", attempts=1),
        _goal(status="success", finished_at="2026-01-15T11:00:00+00:00", attempts=3),
        _goal(status="fail",    finished_at="2026-01-15T12:00:00+00:00", attempts=2),
    ]
    result = aggregate_report_data(goals, days=None)
    idx = result["buckets"].index("2026-01-15")
    # 2 goals had attempts > 1
    assert result["chart2_bar"][idx] == 2
    # avg attempts = (1 + 3 + 2) / 3 = 2.0
    assert result["chart2_line"][idx] == 2.0


def test_token_aggregation():
    goals = [
        _goal(
            status="success",
            finished_at="2026-01-15T10:00:00+00:00",
            input_tokens=100,
            cached_input_tokens=50,
            output_tokens=30,
        ),
        _goal(
            status="fail",
            finished_at="2026-01-15T12:00:00+00:00",
            input_tokens=200,
            cached_input_tokens=0,
            output_tokens=80,
        ),
    ]
    result = aggregate_report_data(goals, days=None)
    idx = result["buckets"].index("2026-01-15")
    assert result["chart3_input"][idx] == 300
    assert result["chart3_cached"][idx] == 50
    assert result["chart3_output"][idx] == 110


def test_cost_per_success_excludes_null_cost():
    goals = [
        _goal(status="success", finished_at="2026-01-15T10:00:00+00:00", cost_usd=None),
        _goal(status="success", finished_at="2026-01-15T11:00:00+00:00", cost_usd=10.0),
    ]
    result = aggregate_report_data(goals, days=None)
    # Only the goal with known cost contributes
    assert "2026-01-15" in result["chart4_buckets"]
    idx = result["chart4_buckets"].index("2026-01-15")
    assert result["chart4_values"][idx] == 10.0


def test_cost_per_success_averages_bucket():
    goals = [
        _goal(status="success", finished_at="2026-01-15T10:00:00+00:00", cost_usd=8.0),
        _goal(status="success", finished_at="2026-01-15T11:00:00+00:00", cost_usd=12.0),
    ]
    result = aggregate_report_data(goals, days=None)
    idx = result["chart4_buckets"].index("2026-01-15")
    assert result["chart4_values"][idx] == 10.0


def test_fail_goals_excluded_from_chart4():
    goals = [_goal(status="fail", finished_at="2026-01-15T10:00:00+00:00", cost_usd=5.0)]
    result = aggregate_report_data(goals, days=None)
    assert result["chart4_buckets"] == []


def test_granularity_daily_for_short_span():
    # 10 days → daily
    goals = [
        _goal(status="success", finished_at="2026-01-01T10:00:00+00:00"),
        _goal(status="success", finished_at="2026-01-10T10:00:00+00:00"),
    ]
    result = aggregate_report_data(goals, days=None)
    assert result["granularity"] == "day"
    assert len(result["buckets"]) == 10


def test_granularity_weekly_for_long_span():
    # 60 days → weekly
    goals = [
        _goal(status="success", finished_at="2026-01-01T10:00:00+00:00"),
        _goal(status="success", finished_at="2026-03-01T10:00:00+00:00"),
    ]
    result = aggregate_report_data(goals, days=None)
    assert result["granularity"] == "week"
    # All bucket keys should be Mondays
    for b in result["buckets"]:
        dt = datetime.strptime(b, "%Y-%m-%d")
        assert dt.weekday() == 0, f"{b} is not a Monday"


def test_days_filter():
    from datetime import timedelta, timezone

    now = datetime.now(tz=timezone.utc)
    old = (now - timedelta(days=60)).isoformat()
    recent = (now - timedelta(days=5)).isoformat()

    goals = [
        _goal(status="success", finished_at=old),
        _goal(status="success", finished_at=recent),
    ]
    result = aggregate_report_data(goals, days=10)
    # Only the recent goal should be included
    assert sum(result["chart1"]) == 1


# ── render smoke test ─────────────────────────────────────────────────────────


def test_render_html_returns_string_with_key_markers():
    from ai_agents_metrics.html_report import _empty_data

    data = _empty_data()
    html = render_html_report(data, "2026-01-15 12:00 UTC")
    assert "<!DOCTYPE html>" in html
    assert "Codex Metrics" in html
    assert "2026-01-15 12:00 UTC" in html
    assert "DATA" in html


def test_render_html_embeds_chart_data():
    goals = [_goal(status="success", finished_at="2026-01-15T10:00:00+00:00", cost_usd=5.0)]
    data = aggregate_report_data(goals, days=None)
    html = render_html_report(data, "2026-01-15 10:00 UTC")
    # Chart data should be embedded as JSON
    assert '"chart1"' in html
    assert '"buckets"' in html
    assert "2026-01-15" in html


def test_render_html_no_external_urls():
    from ai_agents_metrics.html_report import _empty_data

    data = _empty_data()
    html = render_html_report(data, "2026-01-15 10:00 UTC")
    # No CDN or external script/stylesheet references
    for marker in ["cdn.jsdelivr", "unpkg.com", "cdnjs.cloudflare", "fonts.googleapis"]:
        assert marker not in html, f"Found external URL: {marker}"


def test_embedded_js_is_valid_syntax(tmp_path):
    """Extract the inline <script> from the generated HTML and validate it with node --check.

    This catches TypeScript-only syntax (e.g. `as Type`) accidentally left in
    the embedded JS, which Python tests cannot see.
    """
    import re
    import shutil
    import subprocess

    import pytest

    node = shutil.which("node")
    if node is None:
        pytest.skip("node not available")
    assert node is not None  # narrow type for static analysis

    from ai_agents_metrics.html_report import _empty_data

    data = _empty_data()
    html = render_html_report(data, "2026-01-15 10:00 UTC")

    # Extract content of the first <script> block (no src attribute)
    match = re.search(r"<script(?![^>]*\bsrc\b)[^>]*>(.*?)</script>", html, re.DOTALL)
    assert match, "No inline <script> block found in rendered HTML"

    js_src = match.group(1)
    js_file = tmp_path / "embedded.js"
    js_file.write_text(js_src, encoding="utf-8")

    result = subprocess.run(
        [node, "--check", str(js_file)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"node --check failed — embedded JS has a syntax error:\n{result.stderr}"
    )
