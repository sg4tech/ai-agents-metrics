# Bootstrap QA Hardening Retrospective

## Situation

We added a new `bootstrap` command to initialize `codex-metrics` inside another repository.

The first implementation covered the clean happy path and basic reruns, but it had not yet been reviewed from a stricter QA perspective against partial existing scaffold states, conflict safety, and the actual installed console entrypoint UX.

## What Happened

QA review found three important issues:

1. `bootstrap` failed on partially initialized repositories.
If only one of the expected scaffold files already existed, bootstrap delegated to the old all-or-nothing `init_files()` path and aborted instead of completing the missing pieces.

2. `bootstrap` was not atomic on conflict.
It could create `metrics/` and `docs/codex-metrics.md` and only then fail on a conflicting `docs/codex-metrics-policy.md`, leaving a half-bootstrapped target repository behind.

3. Error UX was only partially fixed.
The script shim and `python -m codex_metrics` had friendly `Error: ...` handling, but the packaged `codex-metrics` console script still pointed directly at raw `main()` and could print a traceback on validation errors.

## Root Cause

The first pass optimized for delivering a working bootstrap path quickly, but it still treated several edge conditions as if they belonged to internal tooling rather than public-facing initialization.

More specifically:

- The implementation reused `init_files()` even though `bootstrap` has different semantics from repository-local `init`.
- Preflight validation and write execution were not separated cleanly, so conflict detection happened too late.
- Entrypoint UX was patched per surface instead of first defining one canonical wrapped console entrypoint and routing everything through it.

## Retrospective

The functional core of the feature was sound, but the quality bar was still set too close to “works in an empty repo” rather than “safe to run in the messy states real repositories drift into”.

The QA pass was valuable because it checked:

- partial scaffold adoption
- destructive failure behavior
- installed-package entrypoint behavior, not just local shim behavior

That review changed the implementation in the right direction:

- bootstrap now plans before writing
- conflicts are rejected before mutation
- partial scaffolds are completed instead of rejected
- all supported entrypoints now share one friendly error-handling path

## Conclusions

- Repository initializer commands need a stronger standard than ordinary local helper commands.
- “Happy path + rerun” is not enough QA coverage for a bootstrap flow.
- Public-facing CLI UX must be verified at the real installed entrypoint, not only through development shims.

## Permanent Changes

- Added regression tests for:
  - partial existing scaffold with only `metrics`
  - partial existing scaffold with only `report`
  - non-destructive conflict handling
  - conflict preview under `--dry-run`
  - relative path rendering for custom output paths
  - clean error output for script, module, and installed-style console entrypoints

- Refactored bootstrap into a preflight/apply structure so validation runs before writes.

- Added a canonical `console_main()` entrypoint and pointed packaged `codex-metrics` at it so all user-facing launch paths share the same error UX.
