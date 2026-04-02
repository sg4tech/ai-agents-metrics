# Experiment: Mini-First Model Transition

## Status

- Draft date: `2026-04-02`
- Owner: `product / metrics`
- Related hypothesis: `H-011` in `docs/product-hypotheses.md`

## Goal

Test whether a mini-first default model policy preserves the quality of repo work while reducing token and dollar cost.

## Why This Exists

The project is already structured to measure goal quality, retry pressure, and known cost. That makes it possible to test a cheaper default model policy without guessing from intuition alone.

This experiment should answer one practical question:

- can we move most work to a mini model and keep the workflow effective?

## Baseline Snapshot

Captured before the policy switch on `2026-04-02` from `./tools/codex-metrics show`:

- Closed product goals: `70`
- Reviewed result fit: `42/70`
- Exact Fit Rate, reviewed subset: `95.24%`
- Attempts per Closed Product Goal: `1.10`
- Known product cost coverage: `60/70`
- Known Product Cost per Success: `2.108564 USD`
- Known Product Cost per Success: `1516472.23 tokens`
- Known total cost: `243.005948 USD`
- Known total tokens: `176079912`
- Entry failure reasons:
  - `model_mistake: 2`
  - `unclear_task: 1`

## Policy Change Being Tested

Use a mini model as the default for routine Codex work.

Reserve the larger model for:

- hard debugging
- ambiguous refactors
- planning-heavy tasks
- anything that starts to look like model quality is the bottleneck rather than repo complexity

## Measurement Plan

Measure the next batch of work against the baseline using:

- exact-fit rate
- partial-fit rate
- attempts per closed product goal
- known product cost per success
- known total cost
- model-mistake failure pressure

If possible, compare by task class as well:

- docs and policy work
- CLI and domain work
- tests and verification
- debugging or repair work

## Decision Rule

Treat the switch as successful only if:

- cost drops meaningfully
- retry pressure stays flat or improves
- exact-fit quality does not degrade in a way that matters operationally

Treat it as a bad trade if:

- cost savings are erased by retries
- adjacent-work or partial-fit behavior gets worse
- debugging work becomes slower enough to offset the cheaper model

## Recheck Trigger

Re-evaluate after either:

- 10 to 15 closed goals under the new default, or
- two weeks of usage

whichever comes first.

## Notes

- This document is intentionally small and operational.
- It is meant to be the before/after record, not the place where the whole model-selection debate lives.
- If the experiment proves useful, we can later promote the decision into `docs/product-framing.md` or turn it into a more formal playbook.
