# History Audit Command Retro

## Situation

The project reached a point where the metrics history looked more optimistic than the operator experience behind it.

We already knew there were at least a few important patterns hiding behind goal-level success:

- explicit miss followed by recovery
- multi-attempt recoveries
- stale in-progress goals
- partial cost visibility on successful product goals

At the same time, a parallel refactor was actively splitting the CLI into cleaner modules. Any new feature had to respect that structural transition instead of piling more logic into the old hot paths.

## What Happened

- Added a new read-only audit module under `src/codex_metrics/history_audit.py`.
- Kept the feature initially separate from the main CLI wiring to avoid conflicts.
- Once the modular split stabilized, integrated `audit-history` as a first-class command through the new command/runtime boundaries.
- Added focused tests for:
  - pure history-audit rules
  - CLI help exposure
  - script entrypoint
  - package module entrypoint
- Updated the canonical `make verify` path so the new test file is part of the standard quality bar.

## Root Cause

The original metrics model was strong at operational closure, but weak at surfacing places where the history should be reviewed with stricter PM judgment.

That was not primarily a domain-model bug. It was a missing diagnostic layer:

- the system knew a lot
- but it did not yet help the operator audit where the history might be flattering itself

## 5 Whys

1. Why was the history still hard to interpret honestly?
   Because goal-level success collapsed too much nuance into a clean final state.

2. Why did that matter?
   Because the operator cares about "did I get exactly what I wanted?" more than "did this eventually close?"

3. Why was that gap still open?
   Because there was no dedicated audit layer for partial-fit or suspect-success patterns.

4. Why not add that directly into the existing CLI logic?
   Because the CLI was already in the middle of a module split, and piling new feature logic into the hot file would have raised merge risk and design noise.

5. Why was the final approach better?
   Because building the feature first as a pure read-only module preserved clean boundaries, reduced conflict risk, and made the later CLI integration small and testable.

## Theory Of Constraints

The bottleneck was not raw storage or summary calculation.

The real constraint was interpretability:

- the source of truth was already detailed enough
- what was missing was a focused lens that converts stored history into review candidates

So the highest-leverage change was not more schema complexity, but a lightweight audit command that helps the operator see where manual judgment is still needed.

## Retrospective

The good part of this implementation was sequencing:

1. create a pure module
2. test it in isolation
3. integrate it through the new command boundaries
4. upgrade the canonical verification path

That kept the change aligned with SOLID and GRASP-style responsibilities:

- domain heuristics live in their own module
- CLI wiring stays thinner
- verification stays part of the product contract

## Permanent Changes

- Added `src/codex_metrics/history_audit.py` as a dedicated read-only audit layer.
- Added `tests/test_history_audit.py`.
- Added `audit-history` as a CLI command.
- Extended `make verify` and coverage to include the new audit tests.
- Added README command documentation for `audit-history`.
- Preserved compatibility paths while integrating the new command into the split CLI structure.

## Conclusions

- A history-audit feature belongs in the product because summary metrics alone are too optimistic for PM use.
- During structural refactors, new features should prefer clean side modules before touching hot orchestration code.
- The right way to add trust to this metrics system is not only stricter counters, but better diagnostic views on top of the same source of truth.
