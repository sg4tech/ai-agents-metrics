"""Pure domain tests for token-breakdown aggregation."""

from __future__ import annotations

import pytest

from ai_agents_metrics.warehouse.domain import (
    BreakdownAggregator,
    BreakdownDimension,
    BreakdownTokenRecord,
)


def _record(key: str, total: int) -> BreakdownTokenRecord:
    return BreakdownTokenRecord(
        key=key,
        project_cwd="/project",
        input_tokens=total,
        cache_creation_input_tokens=0,
        cached_input_tokens=0,
        output_tokens=0,
        total_tokens=total,
    )


def test_aggregator_ranks_groups_and_builds_remainder() -> None:
    rows = BreakdownAggregator()(
        [_record("large", 30), _record("small", 10), _record("small", 10)],
        BreakdownDimension.MODEL,
        top=1,
    )

    assert [(row.key, row.total_tokens) for row in rows] == [("large", 30), ("other", 20)]
    assert rows[1].is_remainder
    assert rows[1].grouped_row_count == 1
    assert [row.share_of_total for row in rows] == pytest.approx([0.6, 0.4])


def test_aggregator_rejects_top_for_token_categories() -> None:
    with pytest.raises(ValueError, match="--top is not supported"):
        BreakdownAggregator()([], BreakdownDimension.CATEGORY, top=1)
