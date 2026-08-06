# Architecture

**What this document is:** A technical map of the codebase — modules, data flow, storage, and integrations.

**When to read this:**
- Getting started as a contributor
- Looking for where a specific feature lives
- Debugging a data or CLI issue and not sure which layer to look at

**Related docs:**
- [decisions.md](decisions.md) — why key architectural choices were made
- [testing-guide.md](testing-guide.md) — how to test each layer
- [data-schema.md](data-schema.md) — what the stored data looks like
- [warehouse-layering.md](warehouse-layering.md) — rules for what each warehouse layer (`raw_*` / `normalized_*` / `derived_*`) is allowed to contain

---

## Summary

`ai-agents-metrics` is a CLI tool for analyzing AI agent work history, tracking spending, and optimizing workflows.

**Primary layer — history pipeline:** reads raw session files from `~/.codex` or `~/.claude`, extracts retry pressure, token cost, and session timelines, and stores results in a local SQLite warehouse. No prior instrumentation required.

There is no database server, no background process, and no network dependency.

Data flow:

```
CLI entrypoint (cli.py + cli_parsers.py + cli_constants.py)
  ↓  parses args and dispatches handlers through runtime_facade/
Commands (commands/ package)
  ↓  orchestration against a sanctioned runtime surface (CommandRuntime)
History pipeline (history/*)           ← primary analysis layer
  ↓  ingest → normalize → derive from ~/.codex or ~/.claude
  ↓  SQLite warehouse: retry pressure, token cost, session timeline
Reporting (report/)
  ↓  aggregates warehouse signals and renders a self-contained HTML report
```

---

## How to read this

- **New contributor** → Directory Layout → Entry Points → Data and Storage
- **Working on CLI commands** → Entry Points → CLI Entry Points
- **Working on domain validation or aggregation** → Core Domain
- **Working on storage or event replay** → Data and Storage
- **Working on history reconstruction** → History Pipeline
- **Working on hooks, security, or public boundary** → Integrations

---

## Directory Layout

```
ai-agents-metrics/
├── src/ai_agents_metrics/   # Main Python package
├── tests/               # Pytest test suite (grouped by subject area: cli/,
│                        # domain/, history/, reporting/, workflow/, infra/;
│                        # hypothesis strategies in tests/strategies/)
├── scripts/             # Automation and utility scripts
├── config/              # Public boundary rules (TOML)
├── pricing/             # Token pricing data
├── .githooks/           # commit-msg, pre-commit, pre-push hooks
└── pyproject.toml       # Package config, ruff, mypy, pytest settings
```

---

## Package: `src/ai_agents_metrics/`

### Entry Points

| File / Package | Role |
|----------------|------|
| `__init__.py` | Version resolution: git-derived (`commit_count.sha`) with fallback to package metadata |
| `__main__.py` | Enables `python -m ai_agents_metrics` dispatch |
| `cli.py` | CLI dispatcher + facade surface for `scripts/metrics_cli.py` — records invocation, routes `args.command` to handlers, exposes `console_main` |
| `cli_parsers.py` | Argparse parser construction (`build_parser`, per-group `_add_*_parsers` helpers, hidden-command filter) |
| `cli_constants.py` | Path defaults (`METRICS_JSON_PATH`, `CODEX_STATE_PATH`, `CLAUDE_ROOT`, `RAW_WAREHOUSE_PATH`, …) consumed by both `cli.py` and `cli_parsers.py` |
| `commands/` | CLI handlers grouped into `history`, `report`, `install`, and `misc`; `_runtime.py` defines the runtime protocol used by handlers |
| `runtime_facade/` | Concrete runtime surface for history orchestration, reporting, pricing, audits, and installation |

### Core Domain

| File | Role |
|------|------|
| `domain/` | Domain package split into submodules: `models.py` (dataclasses), `serde.py` (from_dict / to_dict — the only place that converts timestamps between `str` and `datetime`), `validation.py`, `aggregation.py`, `ids.py`, `time_utils.py`. Public API re-exported via `domain/__init__.py`. |
| `storage.py` | Atomic file writes and fcntl lockfile helpers |

### History Pipeline

Sequential stages that reconstruct goal history from raw Codex + Claude Code agent state:

```
Codex (~/.codex) or Claude Code (~/.claude)
  ↓  history/ingest/         → .ai-agents-metrics/warehouse.db (raw_* tables)
       ingest/warehouse.py     — schema, SQL helpers, manifest, path resolution
       ingest/codex.py         — Codex adapter (state_5.sqlite, logs_1.sqlite, session JSONL)
       ingest/claude.py        — Claude Code adapter (projects/*.jsonl, subagent files)
       ingest/__init__.py      — orchestrator (ingest_codex_history), IngestSummary, snapshots
  ↓  history/normalize.py    → cleaned warehouse rows (normalized_* tables)
  ↓  history/classify.py     → session kinds (main vs subagent) + practice-event labels
  ↓  history/derive.py       → GoalRecord + AttemptEntryRecord objects (derived_* tables)
       history/derive_build.py    — pipeline stage builders
       history/derive_insert.py   — typed inserts into derived_*
       history/derive_schema.py   — schema for derived tables
  ↓  history/compare.py      → diff against replayed metrics state
       history/compare_store.py  (persistence for compare results)
       history/audit.py          (consistency checks on derived goals)
```

For the layering rules (raw_* byte-perfect, normalized_* typed, derived_* aggregated) see
`warehouse-layering.md`.

### Analysis and Reporting

| File | Role |
|------|------|
| `reporting.py` | Markdown generation, product quality summaries, agent recommendations |
| `cost_audit.py` | Audits missing/incomplete token and cost data; categorises issues |
| `retro_timeline.py` | Derives a retrospective work timeline from goal records |
| `report/html_report.py` | Public facade for the HTML report: re-exports `aggregate_report_data` and `render_html_report` |
| `report/aggregation.py` | Transforms ndjson goals + warehouse rows into chart-ready series; `_apply_token_pricing` applies model-aware pricing |
| `report/buckets.py` | Pure date/time-bucket helpers (parse, bucket key, make buckets) |
| `report/template.py` | Self-contained HTML/CSS/JS template string; no Python logic |

### Integrations

| File | Role |
|------|------|
| `usage/pricing_runtime.py` | Sanctioned application-level pricing API: resolves effective pricing path and loads workspace-aware pricing |
| `usage/resolution.py` | Pricing data loading, usage event parsing, cost computation, and window resolution logic for Claude and Codex sessions |
| `usage/backends.py` | `UsageBackend` Protocol with `ClaudeUsageBackend` and `UnknownUsageBackend` implementations; delegates window resolution to `usage.resolution` |
| `git_hooks.py` | Implements commit-msg validation and pre-push security scanning logic |
| `commit_message.py` | Validates commit subject format (`CODEX-123:` / `NO-TASK:`) |
| `public_boundary.py` | Verifies files against TOML-configured inclusion/exclusion rules |
| `observability.py` | Appends mutation events to `.ai-agents-metrics/events.sqlite` and a debug log |
| `completion.py` | Shell tab-completion helpers |

---

## Data and Storage

**Primary store:** `.ai-agents-metrics/warehouse.db`
- Intermediate cache populated by `history/ingest/` (Codex + Claude adapters)
- Consumed by normalize → classify → derive steps
- Read directly by `show` and `render-html` for token, retry, timeline, and practice data
- `show --json` exposes a versioned warehouse summary contract and does not read the legacy ledger

**Event log:** `.ai-agents-metrics/events.sqlite` + `events.debug.log`
- Append-only mutation audit trail written by `observability.py`

---

## CLI Entry Points

**Installed command:** `ai-agents-metrics` → `ai_agents_metrics.cli:console_main`

Boundary note:

- `cli.py` is the entrypoint module, not the general runtime dependency surface
- `commands/` depends on `runtime_facade/`, not on `cli.py` (enforced by import-linter)
- pricing-aware runtime consumers should go through `usage/pricing_runtime.py`, not ad-hoc pricing-path resolution

Key command groups:

| Group | Commands |
|-------|----------|
| Inspection | `show`, `render-html` |
| History pipeline | `history-ingest`, `history-normalize`, `history-classify`, `history-derive`, `history-update` |
| History audit | `history-compare`, `history-audit`, `audit-cost-coverage`, `derive-retro-timeline` |
| Tooling | `install-self`, `completion`, `verify-public-boundary`, `security` |

---

## Scripts (`scripts/`)

| Script | Purpose |
|--------|---------|
| `metrics_cli.py` | CLI entry point shim for local development |
| `public_overlay.py` | Bidirectional sync between private repo and `oss/` public mirror |
| `build_standalone.py` | Builds self-contained binary distribution |
| `check_live_usage_recovery.py` | Smoke test for live usage data recovery |

---

## Tests (`tests/`)

One test file per module; files are grouped into subject-area subdirectories so
the root shows structure at a glance:

| Subdir | Test file | Covers |
|--------|-----------|--------|
| `cli/` | `test_metrics_cli.py` | Full CLI workflow integration |
| `domain/` | `test_metrics_domain{,_properties}.py` | Domain model logic + hypothesis invariants |
| `history/` | `test_history_{ingest,normalize,normalize_properties,derive,classify,compare,audit,pipeline_json}.py` | Pipeline stages |
| `reporting/` | `test_{html_report,reporting,retro_timeline,show_json}.py` | Analysis and report rendering |
| `workflow/` | `test_workflow_fsm.py`, `test_git_state.py`, `test_commit_message.py` | State machine transitions, git + hook integrations |
| `infra/` | `test_{public_boundary,public_overlay,security,storage_roundtrip,observability,cost_audit}.py` | Boundary rules, sync, event log I/O, observability |
| `strategies/` | `domain.py`, `history.py` | Hypothesis strategies shared across property tests |
| `tests/private/` (private root only) | `test_git_hooks.py`, `test_claude_md.py` | Git hook behavior and doc generation |

`conftest.py` provides shared fixtures (temp metrics paths, fake goal factories,
etc.) plus `find_repo_paths()` — a `[tool.codex_tests]`-marker-based helper for
resolving the repo root from any test subdir. Prefer it over
`Path(__file__).parents[N]` so test paths stay stable when files move between
subdirs.

---

## Code Quality Configuration

| Tool | Config | Settings |
|------|--------|----------|
| **ruff** | `pyproject.toml` | 15 rule categories (B, C4, ERA, F, FURB, I, PERF, PGH, PTH, Q, RET, RSE, SIM, TC, UP); target Python 3.14; line length 100 |
| **mypy** | `pyproject.toml` | `strict = true` at top level (ARCH-030); covers `src/` + `scripts/`; 65/65 files pass `--strict` |
| **import-linter** | `pyproject.toml` | Six architectural contracts: domain/storage/history boundaries, usage-layer restrictions, package modules must not import `cli.py` outside the entrypoint shim |
| **pylint** | `pyproject.toml` + `Makefile` | Full default rule set on the whole project (ARCH-019 … ARCH-023); a small `disable` list documents the few intentionally-off rules |
| **hypothesis** | `pyproject.toml` dev dep | Property-based tests for `domain/aggregation` (8 invariants) and `history/normalize` (8 invariants); strategies in `tests/strategies/` |
| **pytest** | `pyproject.toml` | `pythonpath = ["src"]`, xdist auto workers, 5s default timeout (overridden per-test on hypothesis suites) |
| **coverage** | `pyproject.toml` | Branch coverage, parallel mode, source = `ai_agents_metrics` |

**Makefile targets:** `lint`, `security`, `typecheck`, `test`, `arch-check`, `verify`, `verify-fast`, `coverage`, `package`, public-overlay ops.

**Git hooks (`.githooks/`):**
- `commit-msg` — rejects commits not matching `CODEX-NNN:` or `NO-TASK:` prefix
- `pre-commit` — runs ruff on staged Python files
- `pre-push` — runs `make verify` when Python files are in the push
