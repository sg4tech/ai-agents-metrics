# Manual Goal ID Conflict UX Retro

## Situation

During routine metrics bookkeeping, a new goal was started with an explicit `--task-id` that had already been used by an existing goal.

The updater rejected the command, but the error message pointed at a downstream invariant:

- `goal_type cannot be changed after attempt history exists`

That made the incident initially look like an auto-generated ID regression, even though goal auto-generation had already been implemented and tested.

## What Happened

- The updater already supported auto-generated goal IDs for new goals.
- A new goal was created manually with an already-used `--task-id`.
- The updater loaded the existing goal and then failed on the goal-type-change guardrail.
- The failure was technically correct but semantically unhelpful.
- This created confusion about whether goal auto-generation had regressed.

## Root Cause

The root cause was not ID allocation.

The actual problem was a UX mismatch between:

- the intended default workflow: omit `--task-id` for new goals
- the user-facing guidance and error path, which still treated manual IDs as normal enough that operator behavior could drift back to them

## 5 Whys

1. Why did the incident happen?
   Because a new goal was created with an already-used explicit `--task-id`.

2. Why was an explicit `--task-id` used?
   Because manual IDs still felt like a normal operating path instead of a special-case path.

3. Why did manual IDs still feel normal?
   Because help text and examples still showed explicit IDs prominently for goal creation.

4. Why did the failure look like a deeper bug?
   Because the updater surfaced a later invariant error instead of the earlier, more meaningful conflict message.

5. Why was that dangerous?
   Because it misclassified an operator workflow problem as a possible allocator regression and wasted debugging attention.

## Theory Of Constraints

The constraint here was not the allocator implementation.

The real bottleneck was the operator decision loop:

- the system allowed two competing mental models
  - new goal with explicit manual ID
  - new goal with auto-generated ID
- when both feel equally valid, operators can drift into the older, higher-risk path

Improving allocator internals further would not have solved this. The highest-leverage fix was to make the safer path the clearer path.

## Retrospective

The system already had the right core behavior:

- auto-generated goal IDs
- tests for sequential and concurrent allocation
- hard rejection of invalid goal-type mutation

What was missing was alignment between:

- workflow guidance
- examples
- error semantics

This was a product and usability issue around the tooling, not a metrics-model issue.

## Permanent Changes

- Updated CLI help and examples so new goals default to auto-generated IDs.
- Updated the conflicting manual-ID error message to say that the goal ID already exists and to recommend omitting `--task-id` for auto-generation.
- Reinforced the same default path in `AGENTS.md`.
- Reinforced the same default path in `docs/codex-metrics-policy.md`.

## Conclusions

- Auto-generated IDs were already working; the incident did not expose an allocator bug.
- The real failure mode was ambiguous workflow guidance plus a confusing error message.
- For this tool, safe default paths must be reinforced in three places:
  - help/examples
  - policy/rules
  - error messages
