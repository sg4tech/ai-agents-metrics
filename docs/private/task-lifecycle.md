# Task Lifecycle

This is the working task lifecycle for Codex-assisted engineering in this repository.

Use it as the practical operating model for moving a task from planned work to implementation, review, and completion.

## Roles

### Lead

The lead owns task orchestration:

- choose the right task
- decide when a stage is complete
- decide when the work is ready to close

The lead may be a human or an operator acting in that role, but the responsibility stays explicit.

### Implementer

The implementer owns execution inside the current stage:

- write code and tests
- keep changes aligned to the requested outcome
- avoid expanding the task into adjacent work without a handoff
- report blockers and uncertainty clearly

### Reviewer / QA

The reviewer owns verification:

- inspect the change for defects, regressions, and missing coverage
- leave concrete follow-up comments when something needs to return to implementation
- accept the work only when the change is actually ready

The same person can fill multiple roles, but the mode should still be explicit.

## Stage Meaning

### Planned Work

Work that has been approved but has not started yet.

### Implementation

The task is actively being implemented.

Expected behavior:

- write code
- update or add tests
- keep the task scoped to the agreed outcome
- do not mark the task done before review and validation

### Review

Implementation is ready for review.

Expected behavior:

- review the diff
- leave findings or approval comments
- return to implementation if changes are needed
- keep the task open until the change is accepted

### Completed

Only when the task is fully finished:

- implementation is complete
- review is clean or the remaining comments are explicitly accepted
- relevant checks have passed
- nothing material is left to return to the implementation stage

### Close Criteria

Before closing a task, confirm all of the following:

- the requested outcome matches what was actually built
- review has either approved the change or explicitly accepted any remaining follow-up
- relevant automated checks have passed
- there is no known blocker that would send the task back to implementation

### Definition of Done (thread closing checklist)

Before closing a conversation thread, work through this checklist. Do not ask the user whether to proceed — if an item is incomplete, complete it automatically.

**If the task involved code:**

- Code review was conducted and all comments are resolved
- QA reviewed the change and critical findings are fixed
- Automated tests exist for the new functionality, covering happy path and relevant edge cases

**In all cases:**

- Retrospective: was one needed? if yes, write and commit it to `docs/retros/` now
- Anything from chat that should be preserved has been saved to files (hypotheses, decisions, policy changes, AGENTS.md rules)
- Commit and push are done — do them now if not yet
- If the task included changes to `AGENTS.md`, `docs/private/task-lifecycle.md`, `docs/ai-agents-metrics-policy.md`, or any other policy/rules file: run `git fetch origin master` first, then verify with `git log origin/master -- <file>`. If not merged, flag it to the user before closing — these files are read from master and changes in a feature branch have no effect.

## Transition Rules

The default flow is:

1. planned work -> implementation
2. implementation -> review
3. review -> implementation when review finds issues
4. review -> completed when the work is accepted

Do not silently skip stage boundaries.

If review uncovers a defect, the task goes back to implementation rather than being forced to completion.

## Metrics Commands That Support The Flow

- `ai-agents-metrics start-task` — open an active goal before implementation begins
- `ai-agents-metrics continue-task` — resume the current goal when implementation continues
- `ai-agents-metrics finish-task --status success` — close the goal when the work is accepted
- `ai-agents-metrics finish-task --status fail` — close the goal when the work should stop
- `ai-agents-metrics ensure-active-task` — verify or recover goal bookkeeping before work continues

## Working Rules

- Keep one active goal per task.
- Treat stage changes as explicit handoffs, not background state drift.
- Prefer the smallest useful change that satisfies the task.
