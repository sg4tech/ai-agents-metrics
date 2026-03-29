# Goals Migration Retro

## Situation

The project moved the metrics source of truth from flat task records to a `goals + entries` model.

This migration was driven by a product problem: task-level metrics were overstating success and understating retry cost for one real user-visible outcome, because one coherent outcome had been split across multiple task records.

## What Happened

- The previous model stored one record per task and derived summary metrics directly from those records.
- That worked for simple independent tasks, but it broke down once one product outcome spanned multiple linked records.
- The most visible example was cost tracking:
  - one pricing-only implementation failed to satisfy the real requirement
  - a later automatic-ingestion implementation succeeded
  - task-level metrics could show both records, but they could not represent the whole outcome cleanly
- The model was migrated to:
  - `goals` as the source of product truth
  - `entries` as the detailed operational history
  - effective goal-chain summaries through supersession links
- Entry-level summary was then added so that failed attempts remained visible and did not disappear behind goal-level success.

## Root Cause

The original metrics model was too flat for the reality of the workflow.

It assumed that one record was close enough to one outcome. That assumption broke as soon as the same product goal required a rejected implementation and then a later replacement. The model had no native place to say:

- this is still the same outcome
- this later record replaces the previous one
- the final goal succeeded, but the path included failed attempts

## Retrospective

The migration was successful in the main thing it needed to fix:

- one linked fail plus one linked success can now be represented as one effective goal with multiple attempts
- raw attempt pressure is still visible through entry-level summary

That is a meaningful upgrade in honesty and product usefulness.

The migration was not perfectly smooth. One unsafe validation command temporarily overwrote generated metrics in the working tree. That was recovered from git state and did not become a lasting data loss issue, but it is a real reminder that generated metrics files are production-like artifacts for this repo and should be treated carefully even during migration work.

There is also one important conceptual limitation left: the current goal model is now much better than task-only metrics, but some “goals” are still arguably too granular. In other words, the model is now structurally capable of telling the truth, but the project still needs disciplined goal-boundary decisions to fully benefit from it.

## Conclusions

- The transition to `goals + entries` was successful.
- The new model is materially better aligned with product outcomes than task-only metrics.
- Goal-level success and entry-level failure pressure can now coexist without contradiction.
- The related TODO item can be marked complete because the requested structural transition has been delivered and validated.
- The next quality frontier is no longer the data model itself, but consistent use of the model.

## Permanent Changes

- Keep `goals + entries` as the source of truth.
- Use goal-level metrics for product outcome reporting.
- Keep entry-level summary visible so failure pressure is not hidden.
- Use supersession links when a later record replaces an earlier attempt of the same goal.
- Treat generated metrics files as sensitive repo state during migrations and validation.

## Open Risks

- Goal boundaries can still be chosen too narrowly or too broadly.
- `cost_per_success` remains `n/a` when a successful goal-chain has incomplete cost history across all linked entries.
- The policy language now reflects the new model, but the team still needs practice using it consistently.
