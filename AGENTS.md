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

### General design principles

Apply SOLID, DRY, GRASP, DDD, and Hexagonal/Clean Architecture to new code and refactors. The
project-specific architecture rules above take precedence over the general principles below.

#### SOLID

- **SRP:** One class, one reason to change. Extract pure algorithms and business rules from
  controllers and services into independently testable components.
- **OCP:** Adding a new source, format, or rule should not require modifying existing
  implementations. Design stable extension points where variants are expected.
- **ISP:** Keep interfaces small and specific. Split an interface when consumers depend on only a
  subset of its methods.
- **DIP:** Application and domain logic depend on port interfaces, not concrete infrastructure.
  Database sessions, HTTP clients, and file handles must not enter domain logic.

#### DDD

- **Value objects:** Use `@dataclass(frozen=True)` for domain concepts defined by value rather than
  identity. Do not use mutable domain primitives.
- **Entities:** Give identity only to concepts that require it. Treat raw input rows as
  observations, not canonical entities.
- **Domain services:** Keep business rules pure and free of database, HTTP, and filesystem I/O.
- **Anti-corruption layer:** Normalize external responses and records into typed dataclasses at
  the adapter boundary. Raw external data must not cross into application or domain logic.

#### Hexagonal and Clean Architecture

Dependency direction is `adapter -> application -> domain`; inner layers never import outer
layers.

- **Domain:** Pure Python value objects, entities, domain services, and business rules. No ORM,
  HTTP client, CLI, or filesystem I/O.
- **Application:** Use cases orchestrate domain logic and depend only on domain types and port
  interfaces. They return typed results rather than `dict[str, Any]`.
- **Adapters:** CLI entrypoints, repositories, external clients, and file readers fetch or render
  data and delegate behavior to the application layer. They contain no business rules.
- **Ports:** Keep repository and external-client interfaces on the application side; concrete
  implementations belong to adapters.

#### GRASP

- **Information Expert:** Put behavior with the data required to perform it.
- **Low Coupling:** Minimize dependencies. Reconsider a class with four or more constructor
  dependencies.
- **Controller:** Keep CLI commands and handlers thin: parse input, call a use case, and delegate
  output rendering.
- **Creator:** Use factories or builders for complex objects instead of scattering equivalent
  construction across callers.

#### DRY

- Keep each business rule, formula, or transformation in one canonical location.
- Parameterize tests that repeat the same behavior with different inputs instead of copying test
  bodies.
- Intentional duplication at layer boundaries, such as separate raw and normalized forms, is a
  data-modeling decision rather than a DRY violation.

#### Composition over inheritance

Prefer injecting collaborators and delegating behavior over subclassing. Inherit only when the
subclass is a genuine specialization and satisfies substitution. Extract shared behavior into a
collaborator instead of creating a base class solely for code reuse.

#### Architecture red flags

Stop and reconsider when:

- A module boundary returns `dict[str, Any]` instead of a typed dataclass or domain object.
- A class or function has five or more injected dependencies.
- Business logic lives in a handler, CLI command, or adapter.
- The same rule or transformation appears in multiple places.
- Domain or application logic imports an ORM, HTTP client, or other I/O implementation.
- A private method contains business logic that can be tested without mocks.
- Domain or application logic calls `datetime.now()` or `datetime.utcnow()` instead of receiving
  a timestamp from an adapter.

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

Validate changes in layers: lint, typecheck, focused tests, regression tests, integration checks,
build validation, and runtime checks when applicable. Passing an earlier layer does not prove that
later layers work. A task is complete only when the relevant checks pass or any verification gap
is stated explicitly.

## External tools and APIs

Read official documentation before changing integrations, GitHub Actions, packaging metadata, or
third-party APIs. Verify action repositories and supported refs, packaging fields, API parameters,
and format keys instead of guessing them.

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
or contributor workflow changes. Write identifiers, file names, comments, documentation, and
log messages in English.

Do not duplicate volatile values such as counts, thresholds, or versions in prose when code or
configuration is their canonical source.

Keep each rule in one canonical location and link to detailed documentation instead of copying
large specifications into multiple files.

## Learning loop

When a bug or repeated failure is found, add a permanent guardrail where practical: a test, type,
validation, lint rule, script, or documentation. Do not leave important debugging lessons only in
chat or local agent memory.

## Knowledge persistence

Store durable project knowledge in committed project documentation so it remains available across
agents and machines. Use local agent memory only as an index pointing to canonical repository
documentation. Move substantive project knowledge found only in local memory into the repository
and keep the memory entry as a pointer.

## Git

- Keep commits focused and use short, descriptive subjects.
- Do not rewrite shared history with rebase, pushed-commit amendment, reset, or cherry-pick used
  to relocate commits. Merge branches instead.
- Do not use `git rebase` to incorporate upstream changes; merge the base branch instead.
- Never bypass branch protection, required checks, hooks, or reviews.
- Do not use force pushes unless a repository maintainer explicitly requests one for a known-safe
  recovery operation.
- Before committing from a worktree, verify the current branch and ensure the commit belongs to
  that worktree.
