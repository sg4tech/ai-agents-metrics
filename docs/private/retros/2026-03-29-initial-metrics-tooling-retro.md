# Initial Metrics Tooling Retro

## Situation

The project now has a working Codex metrics workflow with a policy file, a CLI updater script, generated metrics outputs, and automated tests for the main script behavior.

This retrospective captures the first meaningful checkpoint after bootstrapping the workflow and validating that the updater can be used in practice.

## What Happened

- Project rules were formalized in `AGENTS.md`.
- Mandatory operating policy was added in `docs/codex-metrics-policy.md`.
- The main updater was implemented in `scripts/update_codex_metrics.py`.
- Automated tests were added in `tests/test_update_codex_metrics.py`.
- Input validation was tightened so negative token and cost values fail loudly.
- Generated artifacts were produced through the updater:
  - `metrics/codex_metrics.json`
  - `docs/codex-metrics.md`
- Environment validation showed that `python` was not available in the shell, while the project worked through `.venv/bin/python`.
- `pytest` was also missing from the virtualenv at first and had to be installed before the requested test command could run.
- During bookkeeping for this retro task, a dependent pair of `update` commands was accidentally launched in parallel, which created a false impression that the second update could not find the task. The underlying cause was command ordering, not metrics corruption.

## Root Cause

There were two main sources of friction:

1. Environment assumptions were wrong.
   The workflow instructions used `python`, but the actual working interpreter in this repository is currently `.venv/bin/python`, and `pytest` was not yet installed there.

2. Process discipline was incomplete.
   The metrics workflow requires ordered, stateful updates. Running dependent updater commands in parallel introduced a race at the tooling level, even though the script itself behaved correctly once commands were serialized.

## Retrospective

The initial implementation direction was good: small additive changes, tests around behavior, and generated outputs controlled by one script. That part worked.

The main weakness was not product logic but execution hygiene around the environment and task bookkeeping. We reached a stable baseline, but only after verifying the real interpreter path, installing the missing test dependency, and correcting the ordering of metrics updates.

This is a useful early lesson for the project: the metrics system itself is simple, but its credibility depends on disciplined usage. A lightweight tool can still produce confusing signals if orchestration is careless.

## Conclusions

- The project now has a usable source of truth for Codex task metrics.
- The updater script works for `init`, `update`, and `show` in the real repository flow.
- Test coverage exists for core happy paths and several validation cases.
- The current environment should be treated as `.venv`-first until shell-level `python`/tooling assumptions are normalized.
- Dependent metrics operations must be serialized, not parallelized.

## Permanent Changes

- Keep metrics as generated artifacts only; do not edit them manually.
- Always create or continue a task record before substantive work.
- Increment attempts on each real implementation pass.
- Use `.venv/bin/python` for reliable local execution in this repository until the environment is standardized.
- Do not run dependent `scripts/update_codex_metrics.py update` commands in parallel.
- When a workflow failure is caused by environment or orchestration rather than product logic, record that explicitly in notes and retros.

## Next Steps

- Add a small developer bootstrap note that explains the expected interpreter and test command for this repo.
- Consider teaching the updater to surface environment/help diagnostics more clearly if the workflow is expected to be used by others.
- Expand tests for edge cases around task continuation, timestamps, and failure-reason handling across multiple attempts.
- Decide whether `main.py` is intentionally part of the project or just IDE scaffold noise, and clean that boundary up in a future focused task.
