from __future__ import annotations

from codex_metrics import domain, reporting


def _base_metrics() -> dict[str, object]:
    return {
        "summary": domain.empty_summary_block(include_by_task_type=True),
        "goals": [],
        "entries": [],
    }


def test_build_product_quality_summary_uses_effective_product_goals() -> None:
    data = _base_metrics()
    data["goals"] = [
        {
            "goal_id": "goal-a",
            "title": "Original miss",
            "goal_type": "product",
            "supersedes_goal_id": None,
            "status": "fail",
            "attempts": 1,
            "started_at": "2026-03-31T09:00:00+00:00",
            "finished_at": "2026-03-31T09:05:00+00:00",
            "cost_usd": None,
            "tokens_total": None,
            "failure_reason": "validation_failed",
            "notes": None,
            "result_fit": "miss",
        },
        {
            "goal_id": "goal-b",
            "title": "Recovered result",
            "goal_type": "product",
            "supersedes_goal_id": "goal-a",
            "status": "success",
            "attempts": 2,
            "started_at": "2026-03-31T09:06:00+00:00",
            "finished_at": "2026-03-31T09:10:00+00:00",
            "cost_usd": 0.5,
            "tokens_total": 500,
            "failure_reason": None,
            "notes": None,
            "result_fit": "partial_fit",
        },
        {
            "goal_id": "goal-c",
            "title": "Exact fit",
            "goal_type": "product",
            "supersedes_goal_id": None,
            "status": "success",
            "attempts": 1,
            "started_at": "2026-03-31T10:00:00+00:00",
            "finished_at": "2026-03-31T10:05:00+00:00",
            "cost_usd": 1.0,
            "tokens_total": 1000,
            "failure_reason": None,
            "notes": None,
            "result_fit": "exact_fit",
        },
        {
            "goal_id": "retro-1",
            "title": "Retro",
            "goal_type": "retro",
            "supersedes_goal_id": None,
            "status": "success",
            "attempts": 1,
            "started_at": "2026-03-31T11:00:00+00:00",
            "finished_at": "2026-03-31T11:05:00+00:00",
            "cost_usd": 0.2,
            "tokens_total": 200,
            "failure_reason": None,
            "notes": None,
            "result_fit": None,
        },
    ]
    domain.recompute_summary(data)

    summary = reporting.build_product_quality_summary(data)

    assert summary.closed_product_goals == 2
    assert summary.successful_product_goals == 2
    assert summary.failed_product_goals == 0
    assert summary.reviewed_product_goals == 2
    assert summary.unreviewed_product_goals == 0
    assert summary.exact_fit_goals == 1
    assert summary.partial_fit_goals == 1
    assert summary.miss_goals == 0
    assert summary.review_coverage == 1.0
    assert summary.exact_fit_rate_reviewed == 0.5
    assert summary.attempts_per_closed_product_goal == 2.0
    assert summary.known_cost_successes == 2
    assert summary.known_cost_per_success_usd == 0.75
    assert summary.known_cost_per_success_tokens == 750.0


def test_build_product_quality_summary_excludes_failed_goal_cost_from_success_average() -> None:
    data = _base_metrics()
    data["goals"] = [
        {
            "goal_id": "goal-success",
            "title": "Successful goal",
            "goal_type": "product",
            "supersedes_goal_id": None,
            "status": "success",
            "attempts": 1,
            "started_at": "2026-03-31T09:00:00+00:00",
            "finished_at": "2026-03-31T09:05:00+00:00",
            "cost_usd": 1.0,
            "tokens_total": 1000,
            "failure_reason": None,
            "notes": None,
            "result_fit": "exact_fit",
        },
        {
            "goal_id": "goal-fail",
            "title": "Failed goal",
            "goal_type": "product",
            "supersedes_goal_id": None,
            "status": "fail",
            "attempts": 1,
            "started_at": "2026-03-31T10:00:00+00:00",
            "finished_at": "2026-03-31T10:05:00+00:00",
            "cost_usd": 9.0,
            "tokens_total": 9000,
            "failure_reason": "validation_failed",
            "notes": None,
            "result_fit": "miss",
        },
    ]
    domain.recompute_summary(data)

    summary = reporting.build_product_quality_summary(data)

    assert summary.known_cost_successes == 1
    assert summary.known_token_successes == 1
    assert summary.known_cost_per_success_usd == 1.0
    assert summary.known_cost_per_success_tokens == 1000.0


def test_build_quality_review_flags_partial_coverage_and_misses() -> None:
    review = reporting.build_quality_review(
        reporting.ProductQualitySummary(
            closed_product_goals=4,
            successful_product_goals=3,
            failed_product_goals=1,
            reviewed_product_goals=2,
            unreviewed_product_goals=2,
            exact_fit_goals=1,
            partial_fit_goals=0,
            miss_goals=1,
            exact_fit_rate_reviewed=0.5,
            miss_rate_reviewed=0.5,
            review_coverage=0.5,
            attempts_per_closed_product_goal=1.25,
            known_cost_successes=2,
            known_token_successes=2,
            known_cost_per_success_usd=0.5,
            known_cost_per_success_tokens=500.0,
        )
    )

    assert "Product quality review coverage is partial; fit rates reflect a reviewed subset only." in review
    assert "At least one reviewed product miss exists; inspect why the requested outcome was missed." in review
    assert "Product retry pressure looks elevated; review scope clarity and acceptance boundaries." in review


def test_generate_report_md_starts_with_product_quality_section() -> None:
    data = _base_metrics()
    data["goals"] = [
        {
            "goal_id": "goal-1",
            "title": "Exact fit goal",
            "goal_type": "product",
            "supersedes_goal_id": None,
            "status": "success",
            "attempts": 1,
            "started_at": "2026-03-31T09:00:00+00:00",
            "finished_at": "2026-03-31T09:01:00+00:00",
            "cost_usd": 0.25,
            "tokens_total": 1000,
            "failure_reason": None,
            "notes": None,
            "result_fit": "exact_fit",
        }
    ]
    domain.recompute_summary(data)

    rendered = reporting.generate_report_md(data)

    assert "## Product quality" in rendered
    assert "## Product quality review" in rendered
    assert "## Operational summary" in rendered
    assert rendered.index("## Product quality") < rendered.index("## Operational summary")
    assert "- Reviewed result fit: 1/1 closed product goals" in rendered
    assert "- Exact Fit Rate (reviewed): 100.00%" in rendered
