# Decision Log

**What this document is:** Key architectural and design decisions — why things are the way they are.

**When to read this:**
- Wondering why a particular design choice was made
- Considering a change that touches storage, locking, or the data model
- Reviewing the known trade-offs and tracked weaknesses

**Related docs:**
- [architecture.md](architecture.md) — what the system looks like now
- [architecture/README.md](architecture/README.md) — tracked technical debt (ARCH-001 through ARCH-009)

---

## Summary

New entries should follow the format below. Add entries as decisions are made or recalled — not just for new work, but also when the reasoning behind existing choices becomes clear.

```
## Decision title

**Context:** Why this decision was needed.

**Decision:** What was decided.

**Trade-offs:** Known costs or limitations.
```

---

## Chart 3 stacks by model instead of by token category

**Context:** Chart 3 originally stacked input / cached-input / output tokens (or cost). Product QA (ARCH-017) showed this answered "what share is cached?" — a token-composition question — rather than "where is my money going?" — the primary cost-tracking question for a user running multiple models at different prices (e.g. Opus vs Sonnet).

**Decision:** Chart 3 now stacks one series per model. Colors are assigned deterministically from a fixed 8-color palette sorted by model name, so the same model always gets the same color across runs. The reserved "unknown" bucket is pinned last in slate.

**Trade-offs:**
- The token-composition view is no longer directly visible. It can be reconstructed from the warehouse if ever needed.
- In cost mode (pricing available), rows with unknown models are dropped from the chart — we cannot compute USD without pricing. In token mode (no pricing), unknown-model rows accumulate under "unknown" so nothing is silently lost.
- Legend remains clickable, letting users isolate a single model.

**Why this works:** Model breakdown is the actionable cost dimension for agent-assisted workflows. ARCH-016 populated `model` on every warehouse table, making this chart trustworthy from the first render.

---

## html_report.py split into the `report/` subpackage

**Context:** `html_report.py` grew to 1084 lines as the HTML template, aggregation logic, date helpers, and public API accumulated in one file. Diffs and code review were impractical; the ~730-line template string dominated the file.

**Decision:** The file is split into a dedicated `ai_agents_metrics.report` subpackage:
- `report/buckets.py` — pure date/bucket helpers (no I/O, no side effects)
- `report/aggregation.py` — warehouse-only chart aggregation and model-aware token pricing
- `report/template.py` — the HTML/CSS/JS template string (inert data, no Python logic)
- `report/html_report.py` — thin facade; public API (`aggregate_report_data`, `render_html_report`) unchanged

The original split used three underscore-prefixed modules (`_report_aggregation.py`, `_report_buckets.py`, `_report_template.py`) living next to `html_report.py` at the package root. They were later collected into the `report/` subpackage so the top-level listing shows a single unit instead of four cross-coupled files.

**Trade-offs:** Imports move from `ai_agents_metrics.html_report` / `ai_agents_metrics._report_*` to `ai_agents_metrics.report.*`. One-time migration; the symbol names inside the modules are unchanged.

**Why this works:** Each module has exactly one reason to change, and the subpackage boundary matches the dependency cluster that already existed.

---

## Subpackage-grouping heuristic: 3+ tightly-coupled top-level modules

**Context:** After the `report/` and `usage/` extractions (the `usage_*.py` + `pricing_runtime.py` trio moved into `usage/` the same way), we need a rule for when the next grouping is worth doing — otherwise every refactor devolves into debating taste.

**Decision:** Promote top-level modules into a subpackage when **three or more** of them form a directed import cluster. Two files is too thin to justify the restructuring cost (directory, `__init__.py`, importer updates, import-linter contract rewrites). Examples:
- `report/` (4 files: `html_report`, `aggregation`, `buckets`, `template`) — promoted.
- `usage/` (3 files: `backends`, `resolution`, `pricing_runtime` — `backends` imports `resolution`, `pricing_runtime` imports `resolution`) — promoted.
- `git_hooks.py` remains flat; the former manual-tracking `git_state.py` was removed.
- One-file concerns such as `storage.py` stay flat.

When promoting, drop leading underscores from files whose privacy the new package boundary already expresses (`_report_aggregation.py` → `report/aggregation.py`). Collapse the matching `ai_agents_metrics.<module>` entries in import-linter's "no cli import" contract into a single `ai_agents_metrics.<pkg>` entry — `as_packages=True` covers the subtree.

**Trade-offs:** The threshold is a judgement call, not a rigid rule. Two files that are about to grow into three can be grouped pre-emptively if the third is already in a PR. Conversely, three files without real coupling (only thematic similarity) are not a cluster — don't promote.

**Why this works:** The rule matches the observed ROI curve. Two-file groupings save ~3 lines of import-linter config but cost a PR's worth of importer churn; three-file groupings start paying back (import-linter collapse, top-level listing clean-up, localized contract). Beyond the file-count test, the hard signal is internal edges: if the would-be submodules already import each other, the package boundary matches reality.

---

## Shared `_repo_template` fixture in `tests/conftest.py`

**Context:** Five test files (`tests/cli/test_metrics_cli.py` plus four `tests/history/test_history_*.py`) each defined a local `repo` fixture that spawned five git subprocesses per test (`git init`, two `git config`, `git add`, `git commit`). Across ~160 tests this is several hundred subprocess invocations per run. Under xdist parallel workers + the 5s per-test `pytest-timeout` the git spawns queued up during CPU contention and pushed tests over the cliff intermittently (~50% flake rate on 1-CPU CI hardware).

**Decision:** Build a session-scoped `_repo_template` once (`tests/conftest.py`), then have a function-scoped `repo` fixture `cp -rl` (hardlink-copy) from it for each test. The template's files are `chmod 0o555` so accidental writes fail loudly instead of silently poisoning the shared inode. The pattern was originally introduced for the cli test suite (PR #46) and generalized to all subdirs in PR #49.

Two supporting conventions:

1. **Subprocess-heavy tests get an explicit `@pytest.mark.timeout(15)` override**, not a global timeout bump. The 5s default catches runaway loops; bumping it repo-wide would mask real regressions. Tests that legitimately spawn multiple real Python subprocesses (e.g. `test_bootstrap_wrapper_runs_from_repo_root_even_when_invoked_from_other_cwd`, which runs `bootstrap` then the wrapper's `show`) are rare and marked at the call site.

2. **New test subdirectories must not redefine `repo`.** If a test needs a repo variant, extend via a sibling fixture that takes `repo` as input, or factor the divergent setup into an explicit helper. Per-file copies of the heavy fixture were the exact pattern this ADR replaces.

**Trade-offs:** Tests that don't need `src/`, `scripts/`, or `pricing/` now get them as hardlinks. Hardlink cost is near-zero, so the extra files are free; the risk is tests accidentally depending on template-baked state, which the read-only permission guardrail surfaces immediately.

**Why this works:** The session-scoped template amortizes the 5-subprocess git setup across the entire test run. `cp -rl` makes the per-test copy effectively free because no bytes are copied — just inode entries. Flake rate dropped from ~50% to 0 across 5 consecutive full-suite runs without any test skipping or xdist worker tuning.

---

## cli.py as a re-export facade

**Context:** Early in the project, external scripts and tests imported symbols directly from `cli.py` before the module structure was stable.

**Decision:** `cli.py` re-exports ~50 symbols from `domain`, `reporting`, and `storage` to maintain backward compatibility.

**Trade-offs:** Any code importing from `cli` pulls the entire CLI layer as a dependency. Adding a new domain function requires updating the re-export list. This is a known weakness tracked in ARCH-001. ARCH-032 (2026-04-22) removed 9 re-exports that were kept only for a reflective test pattern; `test_metrics_domain.py` now imports directly from `usage.resolution` / `usage.pricing_runtime` / `runtime_facade`.

---

## Oversized-file splits into packages (ARCH-027 / ARCH-028 / ARCH-034)

**Context:** By mid-April 2026 four modules had drifted past 900 lines:
`commands.py` (1340), `runtime_facade.py` (927), `history/ingest.py` (1152),
and `cli.py` (1091). Files that large strain human review and exceed the
single-tool-call budget for AI-agent contributors.

**Decision:** Split each into a package that preserves the import surface.

| Before | After | Direction |
|--------|-------|-----------|
| `commands.py` | `commands/` — `install.py`, `history.py`, `tasks.py`, `report.py`, `misc.py`, `_runtime.py`, `__init__.py` | cluster-per-command |
| `runtime_facade.py` | `runtime_facade/` — `orchestration.py`, `costs.py`, `mutations.py`, `__init__.py` | `mutations → costs → orchestration` |
| `history/ingest.py` | `history/ingest/` — `warehouse.py`, `codex.py`, `claude.py`, `__init__.py` | adapters → warehouse |
| `cli.py` | `cli.py` (dispatch + facade) + `cli_parsers.py` (argparse) + `cli_constants.py` (paths) | extract, not package |

**Why packages, not just more files:** Each `__init__.py` re-exports the
full public surface so existing importers (`from ai_agents_metrics import
commands`, `from ai_agents_metrics.history.ingest import IngestSummary`)
resolve unchanged. `scripts/metrics_cli.py`'s reflective `globals().update(vars(cli))`
shim keeps working without edits. Tests that imported private helpers
(`_encode_claude_cwd`, `_ensure_schema`, etc.) continue to work via
`__init__.py` re-exports.

**Trade-offs:**
- More files: 4 split sites → 17 new files total. `git blame` at file level
  loses continuity (mitigated by atomic move commits).
- Test-only private re-exports in `history/ingest/__init__.py` document
  a minor boundary leak; tracked for future migration.

**Why this works:** Direction-of-dependency is one-way inside each package
(validated by `lint-imports`). No file now exceeds the pylint
`max-module-lines = 1000` threshold. The only remaining `too-many-lines`
suppressions were stale and have been dropped (ARCH-031).

---

## mypy `--strict` globally (ARCH-030)

**Context:** Strict type-checking was partial: `[tool.mypy]` enabled a
handful of individual flags (`check_untyped_defs`, `no_implicit_optional`,
`disallow_incomplete_defs`), and ARCH-029 introduced a per-module override
for `domain/*` and `history/*` using the explicit strict flag set.

**Decision:** Promote `strict = true` to the top-level `[tool.mypy]`
section. All 65 source files (`src/` + `scripts/`) now pass `mypy --strict`.

**Trade-offs:**
- Required three small fixes: a typed local in `usage/backends.py:135`
  (`sqlite3.Cursor.fetchone()` is typeshed-typed `Any | None`), explicit
  `-> ModuleType` annotations on two bootstrap shim files, and `dict` →
  `dict[str, Any]` in one permission-audit helper.
- ARCH-029 had to work around a mypy ≤ 1.20 bug where `strict = true` in a
  per-module override leaks `warn_return_any` into unrelated modules;
  top-level `strict = true` is not affected.

**Why this works:** The codebase was already mostly strict-clean thanks to
years of incremental typing. The cost of turning the screw the rest of the
way was measured (3 fixes total) and locked in via the global config.
