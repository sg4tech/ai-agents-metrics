from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from codex_metrics.domain import (
    EffectiveGoalRecord,
    build_effective_goals,
    goal_from_dict,
)


@dataclass(frozen=True)
class ProductQualitySummary:
    closed_product_goals: int
    successful_product_goals: int
    failed_product_goals: int
    reviewed_product_goals: int
    unreviewed_product_goals: int
    exact_fit_goals: int
    partial_fit_goals: int
    miss_goals: int
    exact_fit_rate_reviewed: float | None
    miss_rate_reviewed: float | None
    review_coverage: float | None
    attempts_per_closed_product_goal: float | None
    known_cost_successes: int
    known_token_successes: int
    known_cost_per_success_usd: float | None
    known_cost_per_success_tokens: float | None


def _effective_goals_from_data(data: dict[str, Any]) -> list[EffectiveGoalRecord]:
    return build_effective_goals([goal_from_dict(goal) for goal in data["goals"]])


def build_product_quality_summary(data: dict[str, Any]) -> ProductQualitySummary:
    effective_goals = _effective_goals_from_data(data)
    closed_product_goals = [
        goal for goal in effective_goals if goal.goal_type == "product" and goal.status in {"success", "fail"}
    ]
    reviewed_product_goals = [goal for goal in closed_product_goals if goal.result_fit is not None]
    exact_fit_goals = [goal for goal in reviewed_product_goals if goal.result_fit == "exact_fit"]
    partial_fit_goals = [goal for goal in reviewed_product_goals if goal.result_fit == "partial_fit"]
    miss_goals = [goal for goal in reviewed_product_goals if goal.result_fit == "miss"]
    successful_product_goals = [goal for goal in closed_product_goals if goal.status == "success"]
    failed_product_goals = [goal for goal in closed_product_goals if goal.status == "fail"]
    known_cost_successes = [goal for goal in successful_product_goals if goal.cost_usd_known is not None]
    known_token_successes = [goal for goal in successful_product_goals if goal.tokens_total_known is not None]
    known_success_cost_total = sum(goal.cost_usd_known or 0.0 for goal in known_cost_successes)
    known_success_token_total = sum(goal.tokens_total_known or 0 for goal in known_token_successes)
    total_closed = len(closed_product_goals)
    reviewed_count = len(reviewed_product_goals)

    return ProductQualitySummary(
        closed_product_goals=total_closed,
        successful_product_goals=len(successful_product_goals),
        failed_product_goals=len(failed_product_goals),
        reviewed_product_goals=reviewed_count,
        unreviewed_product_goals=total_closed - reviewed_count,
        exact_fit_goals=len(exact_fit_goals),
        partial_fit_goals=len(partial_fit_goals),
        miss_goals=len(miss_goals),
        exact_fit_rate_reviewed=(len(exact_fit_goals) / reviewed_count) if reviewed_count else None,
        miss_rate_reviewed=(len(miss_goals) / reviewed_count) if reviewed_count else None,
        review_coverage=(reviewed_count / total_closed) if total_closed else None,
        attempts_per_closed_product_goal=(
            sum(goal.attempts for goal in closed_product_goals) / total_closed if total_closed else None
        ),
        known_cost_successes=len(known_cost_successes),
        known_token_successes=len(known_token_successes),
        known_cost_per_success_usd=(
            known_success_cost_total / len(known_cost_successes) if known_cost_successes else None
        ),
        known_cost_per_success_tokens=(
            known_success_token_total / len(known_token_successes) if known_token_successes else None
        ),
    )


def format_pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.2f}%"


def format_num(value: float | int | None, decimals: int = 2) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, int):
        return str(value)
    return f"{value:.{decimals}f}"


def format_usd(value: float | None) -> str:
    if value is None:
        return "n/a"
    formatted = f"{value:.6f}".rstrip("0").rstrip(".")
    if "." not in formatted:
        return f"{formatted}.00"
    fractional_part = formatted.split(".", maxsplit=1)[1]
    if len(fractional_part) < 2:
        return formatted + ("0" * (2 - len(fractional_part)))
    return formatted


def format_coverage(known_count: int, total_count: int) -> str:
    if total_count == 0:
        return "n/a"
    return f"{known_count}/{total_count}"


def build_operator_review(summary: dict[str, Any]) -> list[str]:
    review: list[str] = []
    product_summary = summary["by_goal_type"]["product"]
    entry_summary = summary["entries"]
    successes = summary["successes"]

    if product_summary["closed_tasks"] == 0:
        review.append("Need more real product goals before trusting workflow conclusions.")
    elif product_summary["closed_tasks"] < 5:
        review.append("Product sample is still small; treat workflow conclusions as provisional.")

    if summary["by_goal_type"]["meta"]["closed_tasks"] > product_summary["closed_tasks"]:
        review.append("Meta work still outweighs product delivery; validate changes on real product goals.")

    if entry_summary["fails"] > 0:
        top_reason = None
        if entry_summary["failure_reasons"]:
            top_reason = max(
                entry_summary["failure_reasons"].items(),
                key=lambda item: item[1],
            )[0]
        if top_reason is None:
            review.append("Retry pressure exists; inspect failed entries and recent attempts.")
        else:
            review.append(f"Retry pressure exists; inspect failed entries, especially {top_reason}.")

    if successes > 0 and summary["known_cost_successes"] < successes:
        review.append("Cost visibility is partial; use known-cost metrics as directional, not final.")

    if summary["complete_cost_successes"] < successes and summary["known_cost_per_success_usd"] is not None:
        review.append(
            "Full cost coverage is still partial; treat complete covered-success averages as strict subset signals."
        )

    if not review:
        review.append("Signals look stable; continue collecting product-goal history before changing the workflow.")

    return review


def build_quality_review(summary: ProductQualitySummary) -> list[str]:
    review: list[str] = []

    if summary.closed_product_goals == 0:
        review.append("No closed product goals yet; quality conclusions are not ready.")
        return review

    if summary.reviewed_product_goals == 0:
        review.append("Product quality review has not started; result-fit signals are still missing.")
    elif summary.unreviewed_product_goals > 0:
        review.append("Product quality review coverage is partial; fit rates reflect a reviewed subset only.")

    if summary.miss_goals > 0:
        review.append("At least one reviewed product miss exists; inspect why the requested outcome was missed.")

    if summary.partial_fit_goals > 0:
        review.append("Reviewed partial-fit outcomes exist; inspect where delivery succeeded only after correction.")

    if summary.attempts_per_closed_product_goal is not None and summary.attempts_per_closed_product_goal > 1.2:
        review.append("Product retry pressure looks elevated; review scope clarity and acceptance boundaries.")

    if not review:
        review.append("Reviewed product quality signals look stable enough to compare workflow changes.")

    return review


def _product_quality_lines(product_quality: ProductQualitySummary) -> list[str]:
    return [
        "## Product quality",
        "",
        f"- Closed product goals: {product_quality.closed_product_goals}",
        (
            f"- Reviewed result fit: {product_quality.reviewed_product_goals}/"
            f"{product_quality.closed_product_goals} closed product goals"
        ),
        f"- Review coverage: {format_pct(product_quality.review_coverage)}",
        f"- Exact fit: {product_quality.exact_fit_goals}",
        f"- Partial fit: {product_quality.partial_fit_goals}",
        f"- Misses: {product_quality.miss_goals}",
        f"- Unreviewed: {product_quality.unreviewed_product_goals}",
        f"- Exact Fit Rate (reviewed): {format_pct(product_quality.exact_fit_rate_reviewed)}",
        f"- Miss Rate (reviewed): {format_pct(product_quality.miss_rate_reviewed)}",
        f"- Attempts per Closed Product Goal: {format_num(product_quality.attempts_per_closed_product_goal)}",
        (
            f"- Known product cost coverage: "
            f"{format_coverage(product_quality.known_cost_successes, product_quality.successful_product_goals)} "
            "successful product goals"
        ),
        f"- Known Product Cost per Success (USD): {format_usd(product_quality.known_cost_per_success_usd)}",
        f"- Known Product Cost per Success (Tokens): {format_num(product_quality.known_cost_per_success_tokens)}",
        "",
        "## Product quality review",
        "",
    ]


def generate_report_md(data: dict[str, Any]) -> str:
    summary = data["summary"]
    goals: list[dict[str, Any]] = data["goals"]
    entries: list[dict[str, Any]] = data["entries"]
    operator_review = build_operator_review(summary)
    product_quality = build_product_quality_summary(data)
    quality_review = build_quality_review(product_quality)

    lines: list[str] = [
        "# Codex Metrics",
        "",
    ]
    lines.extend(_product_quality_lines(product_quality))
    lines.extend(f"- {line}" for line in quality_review)
    lines.extend(
        [
            "",
            "## Operational summary",
            "",
            f"- Closed goals: {summary['closed_tasks']}",
            f"- Successes: {summary['successes']}",
            f"- Fails: {summary['fails']}",
            f"- Total attempts: {summary['total_attempts']}",
            f"- Known total cost (USD): {format_usd(summary['total_cost_usd'])}",
            f"- Known total tokens: {summary['total_tokens']}",
            f"- Success Rate: {format_pct(summary['success_rate'])}",
            f"- Attempts per Closed Goal: {format_num(summary['attempts_per_closed_task'])}",
            f"- Known cost coverage: {format_coverage(summary['known_cost_successes'], summary['successes'])} successful goals",
            f"- Known token coverage: {format_coverage(summary['known_token_successes'], summary['successes'])} successful goals",
            f"- Complete cost coverage: {format_coverage(summary['complete_cost_successes'], summary['successes'])} successful goals",
            f"- Complete token coverage: {format_coverage(summary['complete_token_successes'], summary['successes'])} successful goals",
            f"- Known Cost per Success (USD): {format_usd(summary['known_cost_per_success_usd'])}",
            f"- Known Cost per Success (Tokens): {format_num(summary['known_cost_per_success_tokens'])}",
            f"- Complete Cost per Covered Success (USD): {format_usd(summary['complete_cost_per_covered_success_usd'])}",
            f"- Complete Cost per Covered Success (Tokens): {format_num(summary['complete_cost_per_covered_success_tokens'])}",
            "",
            "## Entry summary",
            "",
            f"- Closed entries: {summary['entries']['closed_entries']}",
            f"- Successes: {summary['entries']['successes']}",
            f"- Fails: {summary['entries']['fails']}",
            f"- Success Rate: {format_pct(summary['entries']['success_rate'])}",
            f"- Known total cost (USD): {format_usd(summary['entries']['total_cost_usd'])}",
            f"- Known total tokens: {summary['entries']['total_tokens']}",
            "",
            "## Operator review",
            "",
        ]
    )
    lines.extend(f"- {line}" for line in operator_review)
    lines.extend(
        [
            "",
            "## By goal type",
            "",
        ]
    )

    failure_reasons = summary["entries"]["failure_reasons"]
    if failure_reasons:
        lines.extend(
            [
                "### Entry failure reasons",
            ]
        )
        for reason, count in failure_reasons.items():
            lines.append(f"- {reason}: {count}")
        lines.append("")

    for task_type in ("product", "retro", "meta"):
        type_summary = summary["by_goal_type"][task_type]
        lines.extend(
            [
                f"### {task_type}",
                f"- Closed goals: {type_summary['closed_tasks']}",
                f"- Successes: {type_summary['successes']}",
                f"- Fails: {type_summary['fails']}",
                f"- Total attempts: {type_summary['total_attempts']}",
                f"- Known total cost (USD): {format_usd(type_summary['total_cost_usd'])}",
                f"- Known total tokens: {type_summary['total_tokens']}",
                f"- Success Rate: {format_pct(type_summary['success_rate'])}",
                f"- Attempts per Closed Goal: {format_num(type_summary['attempts_per_closed_task'])}",
                f"- Known cost coverage: {format_coverage(type_summary['known_cost_successes'], type_summary['successes'])} successful goals",
                f"- Known token coverage: {format_coverage(type_summary['known_token_successes'], type_summary['successes'])} successful goals",
                f"- Complete cost coverage: {format_coverage(type_summary['complete_cost_successes'], type_summary['successes'])} successful goals",
                f"- Complete token coverage: {format_coverage(type_summary['complete_token_successes'], type_summary['successes'])} successful goals",
                f"- Known Cost per Success (USD): {format_usd(type_summary['known_cost_per_success_usd'])}",
                f"- Known Cost per Success (Tokens): {format_num(type_summary['known_cost_per_success_tokens'])}",
                f"- Complete Cost per Covered Success (USD): {format_usd(type_summary['complete_cost_per_covered_success_usd'])}",
                f"- Complete Cost per Covered Success (Tokens): {format_num(type_summary['complete_cost_per_covered_success_tokens'])}",
                "",
            ]
        )

    lines.extend(
        [
            "## Goal log",
            "",
        ]
    )

    if not goals:
        lines.append("_No goals recorded yet._")
        lines.append("")
        return "\n".join(lines)

    for task in sorted(goals, key=lambda x: x.get("started_at") or "", reverse=True):
        lines.extend(
            [
                f"### {task['goal_id']} — {task['title']}",
                f"- Goal type: {task['goal_type']}",
                f"- Supersedes goal: {task.get('supersedes_goal_id') or 'n/a'}",
                f"- Status: {task['status']}",
                f"- Attempts: {task['attempts']}",
                f"- Started at: {task['started_at'] or 'n/a'}",
                f"- Finished at: {task['finished_at'] or 'n/a'}",
                f"- Cost (USD): {format_usd(task.get('cost_usd'))}",
                f"- Tokens: {format_num(task.get('tokens_total'))}",
                f"- Failure reason: {task.get('failure_reason') or 'n/a'}",
                f"- Result fit: {task.get('result_fit') or 'n/a'}",
                f"- Notes: {task.get('notes') or 'n/a'}",
                "",
            ]
        )

    lines.extend(
        [
            "## Entry log",
            "",
        ]
    )
    for entry in sorted(entries, key=lambda x: x.get("started_at") or "", reverse=True):
        lines.extend(
            [
                f"### {entry['entry_id']} — {entry['goal_id']}",
                f"- Entry type: {entry['entry_type']}",
                f"- Inferred: {'yes' if entry.get('inferred') else 'no'}",
                f"- Status: {entry['status']}",
                f"- Started at: {entry['started_at'] or 'n/a'}",
                f"- Finished at: {entry['finished_at'] or 'n/a'}",
                f"- Cost (USD): {format_usd(entry.get('cost_usd'))}",
                f"- Tokens: {format_num(entry.get('tokens_total'))}",
                f"- Failure reason: {entry.get('failure_reason') or 'n/a'}",
                f"- Notes: {entry.get('notes') or 'n/a'}",
                "",
            ]
        )

    return "\n".join(lines)


def print_summary(data: dict[str, Any]) -> None:
    summary = data["summary"]
    operator_review = build_operator_review(summary)
    product_quality = build_product_quality_summary(data)
    quality_review = build_quality_review(product_quality)
    print("Codex Metrics Summary")
    print("Product quality:")
    print(f"Closed product goals: {product_quality.closed_product_goals}")
    print(
        f"Reviewed result fit: {product_quality.reviewed_product_goals}/"
        f"{product_quality.closed_product_goals} closed product goals"
    )
    print(f"Review coverage: {format_pct(product_quality.review_coverage)}")
    print(f"Exact fit: {product_quality.exact_fit_goals}")
    print(f"Partial fit: {product_quality.partial_fit_goals}")
    print(f"Misses: {product_quality.miss_goals}")
    print(f"Unreviewed: {product_quality.unreviewed_product_goals}")
    print(f"Exact Fit Rate (reviewed): {format_pct(product_quality.exact_fit_rate_reviewed)}")
    print(f"Miss Rate (reviewed): {format_pct(product_quality.miss_rate_reviewed)}")
    print(f"Attempts per Closed Product Goal: {format_num(product_quality.attempts_per_closed_product_goal)}")
    print(
        f"Known product cost coverage: "
        f"{format_coverage(product_quality.known_cost_successes, product_quality.successful_product_goals)} "
        "successful product goals"
    )
    print(f"Known Product Cost per Success (USD): {format_usd(product_quality.known_cost_per_success_usd)}")
    print(f"Known Product Cost per Success (Tokens): {format_num(product_quality.known_cost_per_success_tokens)}")
    print("Product quality review:")
    for line in quality_review:
        print(f"- {line}")
    print("Operational summary:")
    print(f"Closed goals: {summary['closed_tasks']}")
    print(f"Successes: {summary['successes']}")
    print(f"Fails: {summary['fails']}")
    print(f"Total attempts: {summary['total_attempts']}")
    print(f"Known total cost (USD): {format_usd(summary['total_cost_usd'])}")
    print(f"Known total tokens: {summary['total_tokens']}")
    print(f"Success Rate: {format_pct(summary['success_rate'])}")
    print(f"Attempts per Closed Goal: {format_num(summary['attempts_per_closed_task'])}")
    print(f"Known cost coverage: {format_coverage(summary['known_cost_successes'], summary['successes'])} successful goals")
    print(f"Known token coverage: {format_coverage(summary['known_token_successes'], summary['successes'])} successful goals")
    print(f"Complete cost coverage: {format_coverage(summary['complete_cost_successes'], summary['successes'])} successful goals")
    print(f"Complete token coverage: {format_coverage(summary['complete_token_successes'], summary['successes'])} successful goals")
    print(f"Known Cost per Success (USD): {format_usd(summary['known_cost_per_success_usd'])}")
    print(f"Known Cost per Success (Tokens): {format_num(summary['known_cost_per_success_tokens'])}")
    print(f"Complete Cost per Covered Success (USD): {format_usd(summary['complete_cost_per_covered_success_usd'])}")
    print(f"Complete Cost per Covered Success (Tokens): {format_num(summary['complete_cost_per_covered_success_tokens'])}")
    print(f"Closed entries: {summary['entries']['closed_entries']}")
    print(f"Entry successes: {summary['entries']['successes']}")
    print(f"Entry fails: {summary['entries']['fails']}")
    print(f"Entry Success Rate: {format_pct(summary['entries']['success_rate'])}")
    print("Operator review:")
    for line in operator_review:
        print(f"- {line}")
    for task_type in ("product", "retro", "meta"):
        type_summary = summary["by_goal_type"][task_type]
        print(
            f"{task_type.title()} goals: {type_summary['closed_tasks']} closed, "
            f"{type_summary['successes']} successes, {type_summary['fails']} fails"
        )
    if summary["entries"]["failure_reasons"]:
        print("Entry failure reasons:")
        for reason, count in summary["entries"]["failure_reasons"].items():
            print(f"- {reason}: {count}")
