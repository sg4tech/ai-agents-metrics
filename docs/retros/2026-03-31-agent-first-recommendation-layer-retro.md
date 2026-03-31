# Retrospective: Agent-First Recommendation Layer Review

## Situation

`codex-metrics` already had stronger product-quality data than before:

- `result_fit`
- product-only retry pressure
- product cost coverage
- agent-first framing

But the product still had a gap between surfacing signals and helping the primary user act on them.

The primary user is now explicit:

- AI agents read the metrics
- AI agents analyze the state
- AI agents produce recommendations

So the important product question was no longer only:

- what is visible?

It had become:

- what should the agent do next?

## What Happened

The reporting surface was reviewed as:

- team lead
- QA
- product demo

The new recommendation layer was validated across both:

- CLI `show`
- generated `docs/codex-metrics.md`

The product now renders an `Agent recommendations` block that gives:

- category
- priority
- diagnosis
- recommended next action

instead of only generic review observations.

## Team Lead Review

Design review outcome:

- the change was made in the correct layer
- heuristics have single ownership in `src/codex_metrics/reporting.py`
- CLI and markdown surfaces reuse the same recommendation logic
- no schema churn was introduced
- the product became more aligned with the agent-first framing

Architecture review outcome:

- the package moved in the right direction for SOLID, DDD, and GRASP concerns
- behavior stayed additive rather than destructive
- reporting logic remained centralized instead of being duplicated across entrypoints

## QA

QA checks performed:

- `make verify` passed with `152` tests
- live CLI smoke via `./tools/codex-metrics show`
- markdown inspection in `docs/codex-metrics.md`
- regression coverage for:
  - recommendation rendering
  - report output
  - product quality summary
  - supporting operational context

QA result:

- the implementation works as designed
- the recommendation layer is stable across both main output surfaces
- canonical verification already covers the new logic

## Product Demo

Before:

- the product could show quality truth
- but it still required the agent to translate that truth into next actions manually

After:

- the product now directly recommends the next step from current signals
- agents can read:
  - low review coverage
  - partial-fit presence
  - product/meta imbalance
  - entry failures
  - cost coverage caveats
- and receive explicit suggested follow-up actions

This is materially closer to the intended product role:

- not only report
- but improve agent analysis quality

## Root Cause

The prior bottleneck was not missing data and not wrong framing anymore.

The remaining gap was actionability:

- metrics were increasingly correct
- summaries were increasingly honest
- but the product still stopped too early at diagnosis

That meant agents still had to infer the operational next step themselves, which reduced the value of the analysis surface.

## 5 Whys

1. Why was the product still not fully aligned with agent use?
   - Because it exposed signals better than it exposed actions.
2. Why did that matter?
   - Because the primary user is an agent that needs to turn signals into recommendations.
3. Why were recommendations missing?
   - Because earlier product work focused first on correctness, coverage, and framing.
4. Why was that sequence reasonable?
   - Because recommendations built on weak data or wrong framing would have optimized the wrong layer.
5. Why did the recommendation layer become the next right step?
   - Because once data and framing were strong enough, actionability became the new bottleneck.

## Theory of Constraints

The constraint had moved again.

It was no longer:

- cost recovery
- summary truthfulness
- human-versus-agent framing

It had become:

- turning trustworthy metrics into trustworthy next actions for agents

So another data-model change or another framing document would have optimized a non-constraint.

## Conclusions

- The recommendation layer is the right follow-up after product-first summary and agent-first framing.
- The review confirmed that action-oriented reporting is more aligned with the actual user than observation-only reporting.
- The implementation is good enough to treat as a finished checkpoint, not just a prototype.

## Permanent Changes

- `show` now includes an `Agent recommendations` block as a first-class product surface.
- `docs/codex-metrics.md` now includes the same recommendation layer.
- Recommendation heuristics have one owner in `src/codex_metrics/reporting.py`.
- Future product reviews should check not only whether metrics are correct, but whether the product gives the agent a credible next action.
