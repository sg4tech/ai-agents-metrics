# AI Instructions For A New Python Project

Use this file as an operating brief for an AI engineer starting a new Python project.

The goal is not to maximize cleverness.

The goal is to make development faster by reducing:

- wrong turns
- hidden regressions
- brittle workflows
- manual cleanup
- misleading “success”

## Priority Order

Optimize in this order:

1. requested outcome fidelity
2. fast feedback loops
3. safe iteration
4. maintainability
5. polish

Do not trade outcome fidelity for speed theater.

## Core Working Style

- First understand what works now, not what should work in theory.
- Treat assumptions as risks until verified.
- Prefer diagnosis -> guardrail -> verification over clever but weakly defended fixes.
- Prefer small, reviewable, reversible changes over broad rewrites.
- Preserve a working path until the replacement is proven.
- Treat “adjacent but not requested” output as a primary quality failure.
- Before optimizing, identify the current bottleneck and do not polish a non-constraint.

## Start Every Task Correctly

Before implementing:

- restate the requested outcome
- identify constraints and acceptance criteria
- separate verified facts from guesses
- pick the smallest high-leverage next step

If product framing or success criteria are unclear:

- treat drafts as hypotheses
- do not present guessed framing as settled truth

## Project Setup Defaults

For a new Python project, prefer this baseline:

- `src/` layout
- `pyproject.toml` as the primary config file
- `pytest` for tests
- `ruff` for linting
- `mypy` for type checking
- `Makefile` or one canonical verify command

Create one standard local validation entrypoint early, such as:

```bash
make verify
```

It should run, at minimum:

- lint
- typecheck
- tests

## Code Structure

- Keep domain logic separate from CLI, storage, and reporting concerns.
- Use explicit typed boundaries for important records and mutation flows.
- Prefer dataclasses, typed objects, or schemas over shapeless dictionaries at domain boundaries.
- Preserve compatibility surfaces during refactors until a breaking change is intentional and verified.
- Avoid turning one orchestration file into a god-module.

## Testing Strategy

Default to test-first or as close to TDD as practical.

For any meaningful behavior change:

- add or update tests in the same task

For mutating workflows, cover three test buckets when practical:

1. happy path
2. invalid-state rejection
3. output or report consistency after mutation

Use multiple layers of checks:

- unit tests
- regression tests
- CLI/integration tests
- live or smoke checks where real integrations matter

Do not assume synthetic tests are enough for real integration boundaries.

When an integration depends on real external or local runtime artifacts, add an opt-in smoke check.

## Validation Rules

- Fail loudly on invalid state.
- Add strict validation early.
- Encode repeated failure modes as tests, types, validation rules, or guardrails.
- Do not leave important integrity rules as informal convention only.

Examples of high-value validation:

- timestamp ordering
- required status/failure combinations
- acyclic references
- non-negative counters and costs
- stage or lifecycle consistency

## Workflow And Task Boundaries

- Keep one requested outcome as one coherent task or goal.
- Do not split work into many tiny “successes” just to make metrics look good.
- Keep retry history visible.
- If the workflow uses staged handoffs, make the current stage explicit.
- Do not silently jump from requirements to implementation to acceptance without a clear handoff.

For product or delivery work:

- record boundaries close to the real work window
- avoid post-hoc zero-duration closeouts
- keep timing and cost windows honest enough for later analysis

## Metrics And Observability

If the project tracks execution metrics:

- track requested outcomes separately from retry history
- do not let top-line success hide failed attempts
- prefer explicit coverage and covered-subset averages over brittle all-or-nothing KPIs
- add diagnostic audit views before adding more summary polish

If the system says data is missing, verify whether:

- the source data is actually absent
- the extractor is outdated
- the workflow recorded the wrong boundaries

Absence of recovered data is not the same as absence of source data.

## Handling Retrospectives

Retros are useful only if they feed changes back into the system.

When something painful happens:

1. capture the retrospective
2. identify root cause
3. classify the fix:
   - code change
   - test
   - validation rule
   - local workflow rule
   - documentation only
   - no action

Do not promote every lesson into broad policy.

Prefer the narrowest correct scope.

## Release And Automation Principles

- Keep a single source of truth for config and important paths.
- Prefer transparent, reproducible scripts over opaque magic.
- Validate the real artifact that users run, not only the source tree.
- Design bootstrap or initializer flows to support safe reruns and partial existing states.
- Separate preflight checks from writes where possible.

## Things To Avoid

- rewriting large working areas without proving the need
- polishing KPIs before diagnosing the bottleneck
- inventing product framing without user confirmation
- manual testing when automated testing is practical
- documentation-only “fixes” for repeated engineering failures
- broad abstractions added before repeated concrete pain exists

## Good Operating Loop

Use this loop repeatedly:

1. clarify the outcome
2. inspect current behavior
3. diagnose the bottleneck
4. make the smallest useful change
5. add or strengthen guardrails
6. verify strongly
7. capture the lesson if it is likely to repeat

## What “Done” Means

A task is not done when code exists.

A task is done when:

- the requested outcome is actually delivered
- relevant automated verification is green
- important risks are either removed or explicitly stated
- the workflow, metrics, and reporting are consistent with the new behavior

If there is a gap, say so explicitly instead of presenting partial completion as success.
