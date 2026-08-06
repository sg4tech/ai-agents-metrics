# AGENTS.md

This file contains repository-specific instructions for AI coding agents working on
`ai-agents-metrics`.

## Project overview

`ai-agents-metrics` is a Python CLI for analyzing AI-agent history and measuring token cost and
retry pressure. It reads existing Codex and Claude Code session files into a local SQLite
warehouse without manual instrumentation.

There is no database server, background service, or required network connection at runtime.

## Read before changing code

Read the documents relevant to the change:

- `docs/architecture.md` for package structure and dependency direction.
- `docs/testing-guide.md` for test layout, fixtures, and verification commands.
- `docs/history-pipeline.md` and `docs/warehouse-layering.md` for history ingestion,
  normalization, classification, or derivation changes.
- `docs/cli-reference.md` for CLI behavior and compatibility expectations.
- `docs/decisions.md` before changing an established architectural choice.

## Repository layout

- `src/ai_agents_metrics/` contains the Python package.
- `tests/` contains the pytest suite, grouped by subject area.
- `scripts/` contains development and packaging utilities.
- `config/` contains security and publication-boundary rules.
- `pricing/` contains model-pricing data.
- `docs/` contains public product and engineering documentation.

Keep generated files, local databases, logs, secrets, machine-specific paths, and private
workspace material out of the repository.

## Architecture

Preserve the documented dependency direction:

```text
adapters and CLI -> application orchestration -> domain
```

- Domain code is pure Python. It must not perform file, database, HTTP, or CLI I/O.
- Command handlers are thin: parse input, call the runtime/application surface, and render the
  result.
- External data is normalized into typed dataclasses before it crosses into application or
  domain logic.
- Infrastructure implementations depend on application ports, never the reverse.
- Keep provider-specific behavior behind adapters. Prefer one agent-agnostic public API.
- Preserve documented entrypoints, re-exports, and compatibility shims unless a breaking change
  is explicitly intended.
- Put warehouse data in the correct `raw_*`, `normalized_*`, or `derived_*` layer. Do not add a
  table or column before checking `docs/warehouse-layering.md`.
- Model lifecycle-dependent behavior as an explicit state machine rather than scattered guards.

Prefer small, observable changes over broad rewrites. Preserve the working path until its
replacement is covered by tests.

## Python standards

- Support the Python versions declared in `pyproject.toml`.
- Add type annotations everywhere and keep mypy in strict mode.
- Avoid `Any` and untyped dictionaries across module boundaries. Use typed dataclasses or domain
  objects.
- Use `@dataclass(frozen=True)` for immutable value objects.
- Use `pathlib.Path` for filesystem operations.
- Pass timestamps into domain and application logic; do not call `datetime.now()` there.
- Keep configuration such as URLs, timeouts, mappings, and thresholds outside business logic.
- Use structured logging. Mutating or long-running operations must not fail silently.
- Prefer composition and small protocols over inheritance and broad interfaces.
- Do not suppress type or lint errors to make verification pass.

## Tests

Develop test-first where practical. Every behavior change must add or update automated tests.

- Use pytest.
- Use `@pytest.mark.parametrize` when three or more cases share the same assertion shape.
- Put tests in the subject-area directory matching the code under test.
- Reuse fixtures and typed factories instead of copying setup logic.
- Use temporary paths for filesystem and repository tests.
- Do not add test-only escape hatches to production code.

For mutating CLI commands, cover these cases when applicable:

1. Successful mutation.
2. Invalid-state rejection without partial writes.
3. Consistent replayed state and summary after the mutation.

For initializer flows, also test reruns, partial existing state, conflicts, and dry-run behavior.

## Implementation workflow

Use the lightest check that answers the current question while developing:

```bash
.venv/bin/ruff check path/to/changed_file.py
.venv/bin/mypy src/ai_agents_metrics/changed_module.py
.venv/bin/python -m pytest tests/area/test_changed_behavior.py -x -q
```

After structural changes, verify the public entrypoint or compatibility import in addition to
direct module tests.

Run the full gate once after the implementation is stable:

```bash
make verify
```

`make verify` covers lint rules, security checks, strict typing, tests, editable-install
validation, architecture contracts, complexity, and pylint. Do not treat one passing test module
as proof that the full change works.

## CLI, storage, and security rules

- Preserve CLI behavior unless the change explicitly requires a compatibility break.
- Validate inputs before mutation and fail loudly on invalid state.
- Never edit generated summaries as a substitute for changing their source data or generator.
- Use parameterized SQL placeholders for every dynamic value. Never assemble SQL with f-strings
  or string concatenation.
- Separate initializer preflight validation from writes so conflicts cannot leave a partial
  scaffold.
- Cover all side effects: files, locks, temporary directories, subprocesses, and generated state.
- Never commit credentials, tokens, local agent histories, local databases, or user-specific
  filesystem paths.

## Documentation

Update public documentation in the same change when behavior, commands, schemas, architecture,
or contributor workflow changes. Write documentation and code comments in English.

Keep each rule in one canonical location and link to detailed documentation instead of copying
large specifications into multiple files.

## Git

- Keep commits focused and use short, descriptive subjects.
- Do not use `git rebase` to incorporate upstream changes; merge the base branch instead.
- Never bypass branch protection, required checks, hooks, or reviews.
- Do not use force pushes unless a repository maintainer explicitly requests one for a known-safe
  recovery operation.
- Before committing from a worktree, verify the current branch and ensure the commit belongs to
  that worktree.
