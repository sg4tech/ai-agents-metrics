# Testing Guide

**What this document is:** How tests are structured, what helpers are available, and how to write new tests correctly.

**When to read this:**
- Writing a new test or adding coverage to an existing module
- Debugging a test failure and not sure why it is behaving unexpectedly
- Setting up a new worktree or environment and need to run tests

**Related docs:**
- [architecture.md](architecture.md) — what each module does and where it lives

---

## Summary

Tests are split into two styles: unit tests (direct import) and CLI integration tests (in-process by default, subprocess for coverage mode). The canonical entry points are `make verify-fast` and `make verify` (both are final-gate commands before committing — not intermediate diagnostic tools). Every mutating command should have three test buckets: happy path, invalid-state rejection, and summary consistency.

---

## Quick start

```bash
make verify-fast     # lint + typecheck + tests (~55s) — final gate before commit
make verify          # full suite incl. bandit, pylint, complexity (~1.5min) — before committing
make test            # pytest only
make lint            # ruff only
make typecheck       # mypy only
make semgrep-check   # project-specific layer-boundary patterns
python -m pytest tests/history/test_history_summary.py -v # single file
```

Configuration in `pyproject.toml`:
- `pythonpath = ["src"]` — package path is pre-configured; no need to set `PYTHONPATH=src` manually
- Coverage: branch mode, parallel, source = `ai_agents_metrics`

---

## Common workflows

**Before a commit:**
```bash
make verify
```

**Debugging a single test:**
```bash
python -m pytest tests/cli/test_metrics_cli.py::test_name -v -s
```

**Running with subprocess coverage enabled:**
```bash
CODEX_SUBPROCESS_COVERAGE=1 make test
```

---

## Structure: one file per module, grouped by subject area

Tests live under `tests/<area>/test_*.py`. Pick the area that matches the
module under test; if none fits cleanly, add a new subdir rather than
dropping the file at the root.

| Subdir | Test file | Covers |
|--------|-----------|--------|
| `cli/` | `test_metrics_cli.py` | CLI integration (in-process; subprocess for a few script-shim tests) |
| `domain/` | `test_metrics_domain{,_properties}.py` | Domain logic + hypothesis invariants |
| `history/` | `test_history_{ingest,normalize,normalize_properties,derive,classify,compare,audit,pipeline_json}.py` | Pipeline stages |
| `reporting/` | `test_{html_report,show_json}.py` | Warehouse-backed report rendering |
| `workflow/` | `test_commit_message.py` | Commit-message and hook integrations |
| `infra/` | `test_{public_boundary,public_overlay,security}.py` | Boundary and security rules |
| `strategies/` | `domain.py`, `history.py` | Hypothesis strategies shared across property tests |
| `tests/private/` (private root) | `test_git_hooks.py`, `test_claude_md.py` | Git hook behavior, doc generation |

---

## conftest.py

`conftest.py` exposes three shared surfaces every test area imports:

- `run_cli_inprocess()` — in-process CLI runner that calls `main()` directly
  with captured stdout/stderr and a temporary `os.chdir()`. Eliminates Python
  startup overhead (~0.5s per subprocess call) and makes tests ~18x faster
  than a subprocess-based approach. Tests use it by default and fall back to
  real subprocess when `CODEX_SUBPROCESS_COVERAGE=1` is set.
- `find_repo_paths()` — returns `(repo_root, scripts_dir, src_dir)` by walking
  up to the first `pyproject.toml` with a `[tool.codex_tests]` section. Prefer
  it over `Path(__file__).parents[N]` so test paths stay valid when files
  move between subdirs. Cached with `@lru_cache` so it runs once per process.
- `_repo_template` (session-scoped) + `repo` (function-scoped) — a packed git
  baseline built once and hardlinked per test. Replaces the
  per-file `repo` fixtures that used to spawn five git subprocesses per test.
  See the CLI integration section and `decisions.md` for the full rationale.

`conftest.py` also inserts every immediate subdir of `tests/` into `sys.path`,
so cross-test imports like `from test_history_ingest import run_cmd` keep
working from any area.

---

## Two test styles

### 1. Unit tests via direct import

For history queries, domain logic, reporting, and other pure modules.

```python
from ai_agents_metrics.history.summary import load_warehouse_summary

def test_summary_uses_warehouse(tmp_path) -> None:
    summary = load_warehouse_summary(tmp_path / "warehouse.db", tmp_path)
    assert summary.schema_version == 1
```

`@pytest.mark.parametrize` is the standard pattern for validation tests:

```python
@pytest.mark.parametrize(("input", "expected"), [
    ("success", True),
    ("fail", False),
])
def test_something(input: str, expected: bool) -> None:
    ...
```

### 2. CLI integration tests (in-process)

For CLI commands. Use `tmp_path` as an isolated repo root. Tests call the CLI in-process by default via `run_cli_inprocess()` from `conftest.py`:

```python
# Default: in-process call (fast, ~0.01s per invocation)
def run_cmd(tmp_path: Path, *args: str, extra_env=None) -> subprocess.CompletedProcess[str]:
    ...

# Subprocess: only for tests that need real process isolation
# (install-self, script shim, or module entrypoint)
def _run_cmd_subprocess(tmp_path: Path, *args: str, extra_env=None) -> subprocess.CompletedProcess[str]:
    ...

# Module entrypoint: tests python -m ai_agents_metrics (always subprocess)
def run_module_cmd(tmp_path: Path, *args: str, extra_env=None) -> subprocess.CompletedProcess[str]:
    ...
```

A per-test timeout of 5 seconds is enforced via `pytest-timeout` (`pyproject.toml`). Any new test exceeding this limit should use in-process execution or be investigated for unnecessary overhead. Tests that legitimately spawn multiple real Python subprocesses (not the in-process fast path) are rare — when one is unavoidable, override explicitly at the call site with `@pytest.mark.timeout(15)` rather than bumping the repo-wide default. Masking the 5s gate globally would also hide real regressions elsewhere.

**The `repo` fixture (shared across all test subdirs):** `tests/conftest.py`
ships a session-scoped `_repo_template` (git-initialized repo with `src/`,
`scripts/`, `pricing/`, and a packed baseline commit) that the function-scoped `repo`
fixture hardlinks into each test's `tmp_path`. The same fixture
serves `cli/`, `history/`, and any future subdir — do not redefine `repo`
locally (the five local copies that used to spawn `git init` + two `git config`
+ `git add` + `git commit` per test were the dominant xdist flake source on
1-CPU runners and were removed in PR #49; see `decisions.md`).

Template files are `chmod a-w` after build, so any `write_text()` on a
template-originated path (`src/**`, `scripts/metrics_cli.py`,
`pricing/model_pricing.json`, `.git/**`) will raise `PermissionError` — this is
intentional: overwriting a hardlinked file would mutate the shared inode and
poison the template for every subsequent test. Create new files under `src/`
(e.g. `worktree_change.py`) or new top-level paths instead. If a test needs a
variant repo state, extend via a sibling fixture that takes `repo` as input
rather than duplicating the template build.

Parser-surface test pattern:

```python
from ai_agents_metrics.cli_parsers import build_parser

def command_choices() -> set[str]:
    parser = build_parser()
    action = next(item for item in parser._actions if item.dest == "command")
    return set(action.choices)

def test_primary_commands_are_available() -> None:
    assert {"history-update", "show", "render-html"} <= command_choices()
```

---

## Testing with SQLite (history pipeline)

Tests for `history_ingest` / `history_normalize` / `history_derive` require creating SQLite databases with the correct schema.

`create_codex_usage_sources(repo, ...)` in `cli/test_metrics_cli.py` creates:
- `codex_state.sqlite` with a `threads` table
- `codex_logs.sqlite` with a `logs` table

This is a test double for the real `~/.codex/state_5.sqlite` and `~/.codex/logs_1.sqlite`. Usage pattern:

```python
def test_ingest(tmp_path: Path) -> None:
    state_path, logs_path = create_codex_usage_sources(
        tmp_path,
        thread_id="thread-abc",
        model="gpt-5",
        input_tokens=1000,
    )
    summary = ingest_codex_history(
        source_root=tmp_path,
        warehouse_path=tmp_path / "warehouse.sqlite",
    )
    assert summary.threads_ingested == 1
```

---

## Testing architectural boundaries

Test each layer through its own public surface. Replace the next layer with a
small typed fake; do not pull infrastructure upward merely to make a test
convenient.

| Layer under test | Invoke | Replace | Must not use |
|---|---|---|---|
| CLI command | Handler or CLI entrypoint | Runtime protocol | SQLite, application internals |
| Application use case | Typed request and use-case class | Port implementations | Filesystem, SQLite, concrete adapters |
| Persistence adapter | Adapter public method | Nothing below the adapter | CLI handlers, HTML orchestration |
| Renderer or domain function | Pure public function | I/O inputs with typed values | Runtime facade, database |

For report changes this maps to:

- `tests/cli/test_report_command.py` — command-to-runtime delegation and output side effects;
- `tests/reporting/test_report_application.py` — report orchestration with fake query and pricing ports;
- `tests/reporting/test_sqlite_report_query.py` — real SQLite queries against temporary databases;
- `tests/reporting/test_html_report.py` — pure aggregation and HTML rendering.

Warehouse breakdown coverage follows the same split: application tests use fake gate and query
ports, SQLite adapter tests own persistence mapping, domain tests own aggregation rules, and a
small warehouse-backed test pins the composed behavior.

A test is at the wrong boundary when changing SQL breaks a CLI delegation test,
changing console text breaks an adapter test, or an application test needs a
temporary database. Move that assertion to the test for the layer that owns the
behavior.

When adding a new command capability, define the typed runtime/application
operation before implementing the handler. Add or extend an import-linter
contract when a forbidden dependency can be expressed statically.

---

## Coverage with subprocess

Tests that invoke the CLI via `subprocess` are not covered by default.
To enable: `CODEX_SUBPROCESS_COVERAGE=1 make test`.
`build_cmd` and `run_module_cmd` automatically switch to `coverage run --parallel-mode`.

---

## Common pitfalls

**PYTHONPATH in a worktree:**
`.venv` is a symlink to the main repo. In a worktree, always use `PYTHONPATH=src` or run via `make`.

**Test reading real agent history:**
CLI integration tests must use temporary source roots and warehouse paths; never read or modify the developer's real `~/.codex`, `~/.claude`, or `.ai-agents-metrics/warehouse.db` data.
