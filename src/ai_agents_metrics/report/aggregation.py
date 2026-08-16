"""Warehouse-only chart-data aggregation for the HTML report."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from .buckets import _bucket_key, _make_buckets, _parse_date

_MODEL_UNKNOWN_LABEL = "unknown"
_CHART5_TOP_N = 15
_CHART5_AGENT_KINDS = frozenset({"Agent", "agent", "agent_spawn", "subagent"})
_CHART5_SKILL_KINDS = frozenset({"Skill", "skill", "skill_invocation"})
_MODEL_COLORS = ("#2563eb", "#16a34a", "#ea580c", "#9333ea", "#0891b2", "#dc2626")


@dataclass(frozen=True)
class TokenReportRow:
    timestamp: str
    model: str | None
    model_provider: str | None
    input_tokens: int
    cache_creation_input_tokens: int
    cached_input_tokens: int
    output_tokens: int
    total_tokens: int


def _parse_utc(value: str) -> datetime | None:
    parsed = _parse_date(value)
    if parsed is None:
        return None
    return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)


def _apply_token_pricing(
    row: TokenReportRow,
    pricing: dict[str, dict[str, float | None]] | None,
) -> float | None:
    if pricing is None:
        return float(row.total_tokens)
    rates = pricing.get(row.model or "") if row.model else None
    if not rates:
        return None

    if row.model_provider == "openai":
        uncached_input = max(row.input_tokens - row.cached_input_tokens, 0)
    elif row.model_provider == "anthropic":
        uncached_input = row.input_tokens
    elif row.cached_input_tokens or row.cache_creation_input_tokens:
        return None
    else:
        uncached_input = row.input_tokens

    cached_rate = rates.get("cached_input_per_million_usd")
    cache_creation_rate = rates.get("cache_creation_per_million_usd")
    if row.cached_input_tokens and cached_rate is None:
        return None
    if row.cache_creation_input_tokens and cache_creation_rate is None:
        return None
    return (
        uncached_input * (rates.get("input_per_million_usd") or 0.0)
        + row.cache_creation_input_tokens * (cache_creation_rate or 0.0)
        + row.cached_input_tokens * (cached_rate or 0.0)
        + row.output_tokens * (rates.get("output_per_million_usd") or 0.0)
    ) / 1_000_000


def _practice_chart(rows: list[tuple[str, str, int]] | None) -> dict[str, Any]:
    per_name: dict[str, dict[str, int]] = {}
    total = 0
    for name, kind, count in rows or []:
        if not name or count <= 0:
            continue
        bucket = "agent" if kind in _CHART5_AGENT_KINDS else "skill" if kind in _CHART5_SKILL_KINDS else "other"
        per_name.setdefault(name, {"agent": 0, "skill": 0, "other": 0})[bucket] += count
        total += count
    top = sorted(per_name.items(), key=lambda item: (-sum(item[1].values()), item[0]))[:_CHART5_TOP_N]
    return {
        "labels": [name for name, _ in top],
        "agent": [values["agent"] for _, values in top],
        "skill": [values["skill"] for _, values in top],
        "other": [values["other"] for _, values in top],
        "total_events": total,
        "shown_events": sum(sum(values.values()) for _, values in top),
        "source": "warehouse" if top else "none",
    }


def _empty_data(state: dict[str, str], practice: dict[str, Any]) -> dict[str, Any]:
    return {
        "granularity": "day", "buckets": [],
        "chart1_threads": [],
        "chart2_bar": [], "chart2_line": [],
        "chart3_mode": "tokens", "chart3_series": [],
        "chart5": practice,
        "history_date_from": None, "history_date_to": None,
        "warehouse_state": state, "summary": None,
    }


def aggregate_report_data(  # pylint: disable=too-many-locals
    *,
    warehouse_sessions: dict[str, dict[str, int]],
    warehouse_tokens: list[TokenReportRow],
    days: int | None = None,
    pricing: dict[str, dict[str, float | None]] | None = None,
    warehouse_practice: list[tuple[str, str, int]] | None = None,
    warehouse_state: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build report charts exclusively from derived warehouse rows."""
    state = warehouse_state or {"status": "ok"}
    practice = _practice_chart(warehouse_practice)
    token_rows = warehouse_tokens
    session_rows = warehouse_sessions
    if days is not None:
        cutoff = datetime.now(tz=UTC) - timedelta(days=days)
        token_rows = [
            row
            for row in token_rows
            if (dt := _parse_utc(row.timestamp)) is not None and dt >= cutoff
        ]
        session_rows = {day: values for day, values in session_rows.items()
                      if (dt := _parse_utc(day)) is not None and dt >= cutoff}
    dates = [
        dt for row in token_rows if (dt := _parse_utc(row.timestamp)) is not None
    ]
    dates.extend(dt for day in session_rows if (dt := _parse_utc(day)) is not None)
    if not dates:
        return _empty_data(state, practice)
    earliest, latest = min(dates), max(dates)
    granularity = "day" if (latest - earliest).days <= 30 else "week"
    buckets = _make_buckets(earliest, latest, granularity)
    threads = dict.fromkeys(buckets, 0)
    sessions = dict.fromkeys(buckets, 0)
    for day, values in session_rows.items():
        if (dt := _parse_utc(day)) is None:
            continue
        bucket = _bucket_key(dt, granularity)
        if bucket in threads:
            threads[bucket] += values.get("threads", 0)
            sessions[bucket] += values.get("sessions", 0)
    effective_pricing = pricing or None
    if effective_pricing is not None:
        for row in token_rows:
            if (dt := _parse_utc(row.timestamp)) is None:
                continue
            if _bucket_key(dt, granularity) not in threads:
                continue
            if _apply_token_pricing(row, effective_pricing) is None:
                effective_pricing = None
                break

    by_model: dict[str, dict[str, float]] = {}
    for row in token_rows:
        if (dt := _parse_utc(row.timestamp)) is None:
            continue
        bucket = _bucket_key(dt, granularity)
        value = _apply_token_pricing(row, effective_pricing)
        if bucket not in threads or value is None:
            continue
        by_model.setdefault(
            row.model or _MODEL_UNKNOWN_LABEL, dict.fromkeys(buckets, 0.0)
        )[bucket] += value
    series = [
        {
            "name": model,
            "color": _MODEL_COLORS[index % len(_MODEL_COLORS)],
            "values": [round(values[b], 6) for b in buckets],
        }
        for index, (model, values) in enumerate(sorted(by_model.items()))
    ]
    total_threads = sum(threads.values())
    total_sessions = sum(sessions.values())
    return {
        "granularity": granularity, "buckets": buckets,
        "chart1_threads": [threads[b] for b in buckets],
        "chart2_bar": [sessions[b] for b in buckets],
        "chart2_line": [round(sessions[b] / threads[b], 2) if threads[b] else None for b in buckets],
        "chart3_mode": "cost" if effective_pricing else "tokens", "chart3_series": series,
        "chart5": practice,
        "history_date_from": earliest.strftime("%Y-%m-%d"), "history_date_to": latest.strftime("%Y-%m-%d"),
        "warehouse_state": state,
        "summary": {
            "total_threads": total_threads,
            "total_sessions": total_sessions,
            "date_from": earliest.strftime("%Y-%m-%d"),
            "date_to": latest.strftime("%Y-%m-%d"),
        },
    }
