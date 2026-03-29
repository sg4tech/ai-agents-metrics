# Codex Metrics Policy

This policy defines the minimum workflow for tracking Codex-assisted engineering work in a repository.

## Purpose

Use this policy to answer four practical questions:

1. Are requested outcomes being completed successfully?
2. How much retry pressure was required?
3. What failure modes keep repeating?
4. What known token or USD cost was spent?

## Core Rules

- Metrics bookkeeping is mandatory.
- Metrics bookkeeping is mandatory for Codex-assisted engineering work.
- Track one requested outcome as one goal.
- Track retries and implementation passes as attempt history, not as separate unrelated goals.
- Do not manually edit generated metrics files when the CLI can regenerate them.
- Summary values must be derived from stored records, not hand-written.

## Source Of Truth

- Structured metrics: `metrics/codex_metrics.json`
- Generated report: `docs/codex-metrics.md`

If they disagree, the structured metrics file wins.

## Required Goal Workflow

### At Goal Start

1. Create or continue the correct goal.
2. Set `goal_type` explicitly for new goals.
3. Set status to `in_progress`.
4. Start attempts at `0`.

### On Each Attempt

1. Increment attempts.
2. Record notes when useful.
3. Record cost or tokens when known.
4. Record one dominant failure reason when the attempt failed.

### On Goal Completion

1. Set final status to `success` or `fail`.
2. Set `finished_at`.
3. Recompute summary values.
4. Regenerate the report.

## Allowed Goal Types

- `product`
- `retro`
- `meta`

Use:

- `product` for delivery work
- `retro` for retrospective analysis and writeups
- `meta` for bookkeeping, policy, audits, and tooling governance

## Validation Rules

- `success` must not have `failure_reason`
- `fail` must have `failure_reason`
- closed goals must have at least one attempt
- `finished_at` must be empty for `in_progress`
- `finished_at` must not be earlier than `started_at`

## Standard Commands

Initialize the scaffold:

```bash
codex-metrics bootstrap
```

Create or continue a goal:

```bash
codex-metrics update --title "Add CSV import" --task-type product --attempts-delta 1
```

Close a goal:

```bash
codex-metrics update --task-id <goal-id> --status success --notes "Validated"
```

Review the current summary:

```bash
codex-metrics show
```
