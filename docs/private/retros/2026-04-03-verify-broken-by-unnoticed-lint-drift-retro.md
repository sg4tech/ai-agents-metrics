# Retrospective: `make verify` broken by unnoticed lint drift

Linear issue: `CODEX-33`

## Situation

We expected the repository to be in a locally verifiable state after the recent immutability-related work and retrospective follow-up.

Instead, a fresh `make verify` on April 3, 2026 failed immediately at the lint layer:

- `ruff check .`
- `I001 Import block is un-sorted or un-formatted`
- failing file: `tests/test_update_codex_metrics.py`

This was discovered only after we chased a separate stream of pytest cleanup warnings caused by historical immutable temp files.

## What Happened

Recent work touched the import block near the top of `tests/test_update_codex_metrics.py` in several separate commits:

- `ff150a70` added the `sys.path` bootstrap around `ABS_SRC`
- `b815df1a` added `import codex_metrics as codex_metrics_pkg`
- `22aaf0e6` added one `usage_backends` import
- `ac225d9e` added another `usage_backends` import
- `0a33aec4` added `storage`
- `1702e56e` added `file_immutability`

The resulting block remained functionally correct for Python execution, but it drifted out of Ruff's import-order formatting expectations.

Because the immediate debugging session was focused on pytest permission warnings, we initially looked at the wrong symptom cluster. Once the stale `garbage-*` directories were cleaned and the requested focused test passed, the broader repo verification exposed the real blocking issue: lint had already been red.

## Root Cause

The immediate cause was simple: a test file import block was edited incrementally without being normalized by Ruff before the branch was left in a "done" state.

The deeper cause was process drift:

- we treated the successful focused test/debug outcome as evidence that the overall task state was healthy
- we did not re-run the repository's canonical verification entrypoint after the later test-file edits landed
- we allowed a retrospective/cleanup checkpoint to close without re-validating the full repository contract

## 5 Whys

1. Why did `make verify` fail?
Because Ruff rejected the import block in `tests/test_update_codex_metrics.py`.

2. Why was the import block invalid?
Because multiple follow-up edits appended imports without re-sorting or formatting the full block.

3. Why was that not caught immediately?
Because the debugging loop concentrated on pytest cleanup warnings and a single requested test target, not on the full verification stack.

4. Why did we accept that narrower signal?
Because we implicitly treated "the reproduced symptom is gone" as equivalent to "the repository is green."

5. Why did that assumption survive?
Because the workflow did not enforce a final `make verify` checkpoint before we considered the earlier immutability incident resolved.

## Theory Of Constraints

The bottleneck here was not the immutability implementation itself and not pytest. The active constraint was verification discipline at task close-out.

Once work spanned multiple commits and two symptom streams, the lack of a final canonical verify pass became the limiting factor. Until that check is run, local success on a focused symptom can hide unrelated red status elsewhere in the tree.

## Retrospective

This incident was a classic "wrong failure in the foreground, real failure in the background" problem.

The pytest permission warnings were real, but they were also historical noise from stale temp directories. They consumed attention and made it easier to assume the remaining repository state was mostly fine once that noise was explained.

The more important lesson is not "always suspect lint." The lesson is that when a repository defines a canonical verify entrypoint, no sub-problem is actually complete until that entrypoint is run after the last code or test edit related to the task.

The commit history also shows how small, individually reasonable edits can create formatting drift when they land in separate passes. That is exactly the class of issue automation should catch, which means the human/process failure was not in missing the sort order by eye. The failure was in ending the work without the automation pass that exists to catch it.

## Conclusions

- `make verify` is currently red because of a committed import-order violation, not because of the pytest permission warnings.
- The repository state was not actually re-verified after the last edits to `tests/test_update_codex_metrics.py`.
- A passed focused pytest target did not prove repository health and should not have been treated as closure evidence.
- Historical temp-directory warnings created distraction but were not the active blocker for the repo verify path.

## Permanent Changes

- Tests or code guardrails: after edits to tests or CLI workflow files, run at least the lint layer before considering the task stabilized.
- Tests or code guardrails: keep using the repository's canonical `make verify` as the final gate, not only targeted pytest commands.
- Local `AGENTS.md`: no change proposed. The existing verification rules already describe the correct behavior.
- Retrospective only: document that stale pytest `garbage-*` warnings can obscure the real blocking layer, so symptom cleanup should be followed by a full repo verify pass.

## Classification Of Follow-up

- Tests or code guardrails: fix the import block and rerun `make verify`.
- Retrospective only: preserve this incident as an example of symptom-level success masking repository-level failure.
- No action: no product-policy or production-runtime change is needed from this incident.
