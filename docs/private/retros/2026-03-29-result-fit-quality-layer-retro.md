# Result-Fit Quality Layer Retro

## Situation

The metrics system had already become good at tracking operational closure:

- goals
- attempts
- failures
- retries
- partial cost visibility

But it was still weak at answering the operator's most important product question:

- did the result actually match what was wanted?

Goal-level `success` and `fail` were useful operational states, but they were not sufficient as a quality signal.

## What Happened

- Added an explicit `result_fit` field for `product` goals.
- Supported three reviewed values:
  - `exact_fit`
  - `partial_fit`
  - `miss`
- Exposed it through CLI update flow, validation, and reporting.
- Backfilled only the clearest historical cases:
  - `2026-03-29-007 -> miss`
  - `2026-03-29-008 -> partial_fit`
  - `2026-03-29-069 -> partial_fit`
- Updated `audit-history` so already-reviewed goals stop reappearing as unresolved partial-fit or miss candidates.

## Root Cause

The previous system assumed too much from `success`:

- operational closure
- acceptance
- exact outcome fit

Those are related, but not identical.

The gap mattered because the operator's real quality definition is stronger:

- quality is primarily whether the result was exactly what was wanted

## 5 Whys

1. Why did the metrics still feel too optimistic?
   Because many goals were marked `success` once they operationally closed.

2. Why was that not enough?
   Because some successful goals were only partial recoveries or eventually-corrected outcomes.

3. Why wasn't that already visible?
   Because the system had no separate reviewed quality layer beyond `success` and `fail`.

4. Why not rewrite historical statuses instead?
   Because status still correctly described operational history, and rewriting it would have mixed delivery state with later interpretation.

5. Why was a new field better?
   Because it let the system preserve operational truth while adding product-quality truth on top.

## Theory Of Constraints

The constraint was not data storage.

The source of truth already had enough history to identify:

- explicit misses
- recovery chains
- multi-attempt successes

The real bottleneck was interpretation:

- the system could store the events
- but it could not yet represent the operator's reviewed judgment of the result

So the highest-leverage change was to add a lightweight reviewed quality layer, not another derived aggregate.

## Retrospective

The strongest decision in this change was restraint:

- do not rewrite all historical status values
- do not auto-classify the full past
- do not pretend that heuristics are the same as truth

Instead:

- keep `status` as operational state
- add `result_fit` as reviewed quality state
- backfill only the clearest cases

This preserved trust in the history while making the product more honest.

## Permanent Changes

- Added `result_fit` for `product` goals.
- Added strict validation rules so `result_fit` cannot drift into invalid combinations.
- Added report visibility for `result_fit`.
- Added curated historical backfill for the clearest known quality cases.
- Updated `audit-history` to skip goals that already carry reviewed quality judgments.
- Updated policy and README to reflect the new field.

## Conclusions

- Operational success and outcome fit must remain separate concepts.
- History repair should be curated where confidence is high, not mass rewritten from weak heuristics.
- The metrics system is now more aligned with the real operator definition of quality.
